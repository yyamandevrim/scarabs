"""Host fault injection: analysis availability is distinct from capture health."""
from dataclasses import replace
from threading import Thread
from types import SimpleNamespace
import time
import numpy as np
import pytest
from auth_client import TestClient
from conftest import wait_until
from station import runtime
from station.alarm import Detection
from station.capture import Frame
from station.runtime import Station
from station.web import create_app
from test_capture import EmptyDetector

D = Detection((.1, .1, .4, .4), .8)


class FreshWorker:
    def __init__(self):
        self.sequence = 0
        self.latest = self
    def get(self):
        self.sequence += 1
        return Frame(self.sequence, time.time(), np.zeros((24, 32, 3), np.uint8))
    def status(self):
        return {'connected': True, 'last_frame_at': time.time()}
    def start(self): pass
    def stop(self): pass
    def evidence(self, *args): return []


def fresh_station(config, detector=None):
    station = Station(config, detector=detector or EmptyDetector())
    station.workers = {name: FreshWorker() for name in station.workers}
    return station


def test_retention_fault_is_visible_bounded_and_recovers_while_both_cameras_analyse(config, monkeypatch):
    station = fresh_station(config)
    real_prune = station.store.prune
    failing = True
    def prune(*args):
        if failing:
            raise PermissionError('private detail ' * 1000)
        return real_prune(*args)
    monkeypatch.setattr(station.store, 'prune', prune)
    # Only the runtime scheduling clock advances quickly; real capture/test time stays intact.
    ticks = iter(range(0, 1000000, 61))
    monkeypatch.setattr(runtime, 'time', SimpleNamespace(time=time.time, monotonic=lambda: next(ticks)))
    try:
        station.start()
        with TestClient(create_app(station, manage_lifecycle=False)) as client:
            wait_until(lambda: all(m['analyses'] >= 2 for m in station.metrics.values()))
            body = client.get('/api/status').json()
            assert body['runtime']['analysis_running']
            assert body['runtime']['retention_error']
            assert len(body['runtime']['retention_error']) < 200
            assert 'private detail' not in body['runtime']['retention_error']
            before = {name: m['analyses'] for name, m in station.metrics.items()}
            wait_until(lambda: all(m['analyses'] > before[name] for name, m in station.metrics.items()))
            failing = False
            wait_until(lambda: client.get('/api/status').json()['runtime']['retention_error'] is None)
    finally:
        station.stop()
        station.store.shutdown()
    assert station.status()['runtime']['state'] == 'stopped'
    assert station.status()['runtime']['error'] is None


def test_unexpected_analysis_loop_exit_is_observable(config, monkeypatch):
    station = fresh_station(config)
    def broken(now):
        raise RuntimeError('private loop failure')
    monkeypatch.setattr(station, '_collect_evidence', broken)
    try:
        station.start()
        station.thread.join(2)
        assert not station.thread.is_alive()
        with TestClient(create_app(station, manage_lifecycle=False)) as client:
            health = client.get('/api/status').json()['runtime']
            assert health['state'] == 'failed'
            assert not health['analysis_running']
            assert health['error']
    finally:
        station.stop()
        station.store.shutdown()


def test_failed_predictions_expire_last_observation_clear_overlay_and_require_fresh_votes(config):
    class ControlledWorker(FreshWorker):
        auto = True
        def get(self):
            if self.auto: self.sequence += 1
            return Frame(self.sequence, time.time(), np.full((24,32,3), self.pixel, np.uint8))
    class Detector:
        left = 0
        failing = False
        recovery = False
        def predict(self, image):
            if image[0,0,0] == 0:
                self.left += 1
                if self.left > 3 and not self.recovery:
                    self.failing = True
                    raise RuntimeError('analysis unavailable')
                return [D], {'preprocess_ms':0., 'inference_ms':1., 'analysis_ms':1.}
            return [], {'preprocess_ms':0., 'inference_ms':1., 'analysis_ms':1.}
    detector = Detector()
    station = fresh_station(replace(config, analysis_hz=50, event_timeout=.08), detector)
    for pixel, name in enumerate(station.workers):
        worker = ControlledWorker(); worker.pixel = pixel
        station.workers[name] = worker
    # Exercise real snapshot/event creation; avoid asynchronous clip codecs in this fault test.
    station._submit_clip = lambda pending: None
    try:
        station.start()
        wait_until(lambda: station.store.pending_count() == 1)
        event_id = station.store.events()[0]['id']
        wait_until(lambda: detector.failing)
        before = station.metrics['centre']['analyses']
        wait_until(lambda: station.metrics['centre']['analyses'] >= before+5)
        row = station.store.event(event_id)
        assert row['closed_at'] is not None
        assert station.trackers['left'].events == []
        assert station.detections['left'] == []
        import cv2
        preview = cv2.imdecode(np.frombuffer(station.jpeg('left'), np.uint8), cv2.IMREAD_COLOR)
        assert not preview.any(), 'fresh black input must have no stale coloured annotation'
        assert list(station.trackers['left'].rule.history) == []
        assert station.metrics['left']['pipeline_error'] == 'analysis unavailable'
        assert station.metrics['centre']['pipeline_error'] is None
        station.workers['left'].auto = False
        # Wait until the last in-flight failed analysis is recorded, then give only
        # one new sequence per recovery vote; no wall-clock race for vote counts.
        wait_until(lambda: station.metrics['centre']['analyses'] >= before+7)
        detector.recovery = True
        for vote in range(1,4):
            analyses = station.metrics['left']['analyses']
            station.workers['left'].sequence += 1
            wait_until(lambda: station.metrics['left']['analyses'] > analyses)
            assert station.store.pending_count() == (2 if vote == 3 else 1)
            assert len(station.trackers['left'].rule.history) == vote
        assert station.metrics['left']['pipeline_error'] is None
    finally: station.stop(); station.store.shutdown()
