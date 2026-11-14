"""Capture/display resolution must not be tied to detector input resolution."""
from dataclasses import replace
import time
import cv2
import numpy as np
import pytest
from station.capture import CaptureWorker
from station.runtime import Station
from test_capture import EmptyDetector
from conftest import wait_until


def test_preview_keeps_native_resolution_by_default(config):
    station = Station(config, detector=EmptyDetector())
    try:
        image = np.zeros((720, 1280, 3), np.uint8)
        station.workers['left'].latest.put(image, time.time())
        decoded = cv2.imdecode(np.frombuffer(station.jpeg('left'), np.uint8), cv2.IMREAD_COLOR)
        assert decoded.shape == image.shape
        assert np.array_equal(image, np.zeros_like(image))
    finally:
        station.stop(); station.store.shutdown()


def test_preview_quality_and_optional_width(config):
    image = np.random.default_rng(12).integers(0, 256, (480, 640, 3), dtype=np.uint8)
    station = Station(replace(config, preview_jpeg_quality=98, preview_width=0), detector=EmptyDetector())
    try:
        station.workers['left'].latest.put(image, time.time())
        high = station.jpeg('left')
        station.config = replace(station.config, preview_jpeg_quality=40, preview_width=320)
        low = station.jpeg('left')
        assert len(high) > len(low) * 2
        assert cv2.imdecode(np.frombuffer(low, np.uint8), 1).shape[:2] == (240, 320)
        station.config = replace(station.config, preview_width=1280)
        assert cv2.imdecode(np.frombuffer(station.jpeg('left'), np.uint8), 1).shape[:2] == (480, 640)
        station.workers['left'].latest.clear()
        assert station.jpeg('left') is None
    finally:
        station.stop(); station.store.shutdown()


def test_usb_negotiation_and_no_artificial_upscale(config, monkeypatch):
    calls = []
    class Camera:
        def set(self, key, value): calls.append((key, value)); return True
        def get(self, key):
            return {cv2.CAP_PROP_FPS: 5, cv2.CAP_PROP_FOURCC: cv2.VideoWriter_fourcc(*'MJPG')}.get(key, 0)
        def isOpened(self): return True
        def read(self): time.sleep(.02); return True, np.zeros((480, 640, 3), np.uint8)
        def release(self): pass
    monkeypatch.setattr(cv2, 'VideoCapture', lambda *args: Camera())
    camera = replace(config.cameras[0], kind='usb', source='/dev/v4l/by-path/test', width=1280, height=720,
                     capture_format='MJPG', capture_fps=5)
    worker = CaptureWorker(camera, config)
    worker.watched = None
    worker.start()
    try:
        wait_until(lambda: worker.status()['connected'])
        assert worker.latest.get().image.shape[:2] == (480, 640)
        assert calls.index((cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))) < calls.index((cv2.CAP_PROP_FRAME_WIDTH, 1280))
        assert (cv2.CAP_PROP_FPS, 5) in calls
        state = worker.status()
        assert (state['capture_width'], state['capture_height'], state['capture_format']) == (640, 480, 'MJPG')
        # Evidence never enlarges a smaller source.
        wait_until(lambda: len(worker.ring) > 0)
        assert cv2.imdecode(np.frombuffer(worker.ring[0][1], np.uint8), 1).shape[1] <= 640
    finally: worker.stop()


@pytest.mark.parametrize('options', [{'preview_jpeg_quality': 0}, {'evidence_jpeg_quality': 101}, {'preview_width': -1}])
def test_invalid_picture_settings(config, options):
    with pytest.raises(ValueError): replace(config, **options)


def test_invalid_capture_settings(config):
    for options in ({'capture_format': 'H264'}, {'capture_fps': -2}):
        cameras = [replace(c, **options) if c.name == 'left' else c for c in config.cameras]
        with pytest.raises(ValueError): replace(config, cameras=cameras)


def test_evidence_quality_is_independent_of_preview(config, monkeypatch):
    from station.alarm import Detection
    station = Station(replace(config, preview_jpeg_quality=25, evidence_jpeg_quality=98), detector=EmptyDetector())
    calls = []
    original = cv2.imwrite
    def write(path, image, params):
        calls.append((image.shape, params))
        return original(path, image, params)
    monkeypatch.setattr(cv2, 'imwrite', write)
    try:
        image = np.zeros((720, 1280, 3), np.uint8)
        station.workers['left'].latest.put(image, time.time())
        frame = station.workers['left'].latest.get()
        event_id = station._create_event('left', frame, Detection((.1, .1, .5, .5), .9), time.time())
        saved = cv2.imread(str(station.store.media/(event_id+'.jpg')))
        assert saved.shape == image.shape
        assert calls == [(image.shape, [cv2.IMWRITE_JPEG_QUALITY, 98])]
        station.pending.clear()
    finally:
        station.stop(); station.store.shutdown()


def test_corrupt_yuv_frame_is_a_fault_and_never_reaches_detector(config):
    from threading import Event
    release_bad = Event()
    bad = np.zeros((240, 320, 3), np.uint8)
    bad[:60] = np.random.default_rng(4).integers(0, 256, (60, 320, 3), dtype=np.uint8)
    bad[60:, :, 1] = 154  # OpenCV's BGR result for an unfilled YUYV buffer.
    seen = []
    class Detector(EmptyDetector):
        def predict(self, frame):
            seen.append(frame)
            return super().predict(frame)
    class Camera:
        def isOpened(self): return True
        def get(self, key): return 25
        def read(self):
            time.sleep(.02)
            return True, bad if release_bad.is_set() else np.full((240, 320, 3), 80, np.uint8)
        def release(self): pass
    station = Station(replace(config, retry_seconds=1), detector=Detector(), capture_factory=lambda c: Camera())
    station.start()
    try:
        wait_until(lambda: bool(seen))
        release_bad.set()
        wait_until(lambda: not station.workers['left'].status()['connected'])
        assert 'frame' in station.workers['left'].status()['error'].lower()
        assert station.workers['left'].latest.get() is None
        assert station.jpeg('left') is None
        assert not any(np.array_equal(frame, bad) for frame in seen)
    finally:
        station.stop(); station.store.shutdown()


@pytest.mark.parametrize('image', [None, np.empty((0, 10, 3), np.uint8), np.zeros((10, 10), np.uint8)])
def test_malformed_capture_frame_rejected(image):
    from station.capture import validate_frame
    with pytest.raises(OSError, match='frame'):
        validate_frame(image)
