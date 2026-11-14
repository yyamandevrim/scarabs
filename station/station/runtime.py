"""One shared detector, round-robin analysis, independent capture and local evidence."""
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from pathlib import Path
from threading import Event, Lock, Thread
import logging
import sqlite3
import time
import cv2
from . import clip, datalock
from .alarm import EventTracker
from .capture import CaptureWorker
from .detector import SmokeDetector, annotate
from .centre_views import build_detector
from .led import LedHook
from .machine import machine_identity
from .mcu_bridge import McuBridge
from .storage import EventStore
from .lora.bridge import LoraBridge

class Station:
    def __init__(self, config, detector=None, capture_factory=None):
        self.config = config
        self.detector = detector if detector is not None else build_detector(config, SmokeDetector)
        self.data_lock = datalock.acquire(config.data_dir)
        try:
            self.store = EventStore(config.data_dir)
            self.workers = {c.name: CaptureWorker(c, config, factory=(lambda c=c: capture_factory(c)) if capture_factory else None) for c in config.cameras if c.active}
            self.trackers = {name: EventTracker(config.similarity_iou, config.event_timeout, config.alarm_gap_seconds) for name in self.workers}
            self.led = LedHook(config.led_path)
            self.mcu = McuBridge(self, config.mcu)
            self.stop_event = Event()
            self.lock = Lock()
            self.metrics = {name: {"analyses":0, "preprocess_ms":None, "inference_ms":None, "analysis_ms":None, "analysis_hz":0.0, "pipeline_error":None} for name in self.workers}
            self.pending = []
            self.media_jobs = []
            self.encoder = ThreadPoolExecutor(max_workers=1, thread_name_prefix="evidence", initializer=clip.lower_thread_priority)
            self.clip_timings = deque(maxlen=50)
            self.thread = None
            self.runtime_state = "ready"
            self.runtime_error = None
            self.retention_error = None
            self.lora = LoraBridge(self)
        except BaseException:
            try:
                if hasattr(self, "encoder"):
                    self.encoder.shutdown(wait=True)
            finally:
                try:
                    if hasattr(self, "store"):
                        self.store.shutdown()
                finally:
                    datalock.release(self.data_lock)
                    self.data_lock = None
            raise

    def start(self):
        if self.runtime_state != "ready":
            raise RuntimeError("Station instances can only be started once")
        try:
            self.store.close_previous(time.time())
            self._prune_retention()
            for worker in self.workers.values():
                worker.start()
            self.runtime_state = "running"
            self.thread = Thread(target=self._run_guarded, name="shared-detector", daemon=True)
            self.thread.start()
            self.mcu.start()
            self.lora.start()
        except BaseException:
            self.runtime_state = "failed"
            self.runtime_error = "Station start failed; check local logs"
            self.stop()
            raise

    def stop(self):
        if self.data_lock is None:
            return
        self.lora.stop()
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=30)
            if self.thread.is_alive():
                self.runtime_state = "failed"
                self.runtime_error = "Analysis loop did not stop; journal remains locked"
                raise RuntimeError(self.runtime_error)
        try:
            try:
                for worker in self.workers.values():
                    worker.stop()
                for pending in self.pending:
                    self._submit_clip(pending)
                self.pending.clear()
            finally:
                self.encoder.shutdown(wait=True)
            now = time.time()
            for tracker in self.trackers.values():
                for event in tracker.events:
                    self.store.close_event(event.id, now)
            self.led.set_alarm(False)
        finally:
            try:
                self.mcu.stop()
            finally:
                # No open journal may outlive maintenance exclusion.
                try:
                    self.store.shutdown()
                finally:
                    datalock.release(self.data_lock)
                    self.data_lock = None
        if self.runtime_state != "failed":
            self.runtime_state = "stopped"

    def status(self):
        now = time.time()
        cameras = []
        for camera in self.config.cameras:
            item = asdict(camera)
            item.pop("source")  # Do not expose host paths in the panel.
            if not camera.active:
                item.update(status="inactive", status_text="mounted, inactive", connected=False)
            else:
                state = self.workers[camera.name].status()
                connected = state["connected"] and state["last_frame_at"] is not None and now-state["last_frame_at"] <= self.config.stale_seconds
                with self.lock:
                    item.update(self.metrics[camera.name])
                item.update(state)
                item.update(connected=connected, status="connected" if connected else "disconnected", status_text="connected" if connected else "connection lost")
            cameras.append(item)
        running = self.thread is not None and self.thread.is_alive()
        state = self.runtime_state
        error = self.runtime_error
        if state == "running" and not running and not self.stop_event.is_set():
            state, error = "failed", "Analysis loop stopped unexpectedly"
        return {"cameras": cameras, "runtime": {"state":state, "analysis_running":running, "error":error, "retention_error":self.retention_error}, "analysis_profile":self.config.analysis_profile_status(), "target_analysis_hz":self.config.analysis_hz, "input_size":self.config.input_size, "confidence_threshold":self.config.confidence, "offline":True, "measured_on":machine_identity(), "mcu":self.mcu.status()}

    def _prune_retention(self):
        try:
            self.store.prune(time.time(), self.config.retention_days)
        except (OSError, sqlite3.Error) as exc:
            error = f"Retention unavailable ({type(exc).__name__}); retrying"
            if error != self.retention_error:
                logging.exception("Event retention failed; analysis continues")
            self.retention_error = error
        else:
            self.retention_error = None

    def _run_guarded(self):
        try:
            self._run()
        except Exception:
            logging.exception("Shared analysis loop terminated")
            self.runtime_error = "Analysis loop stopped unexpectedly; check local logs"
        finally:
            if self.runtime_error or not self.stop_event.is_set():
                self.runtime_state = "failed"
                self.runtime_error = self.runtime_error or "Analysis loop stopped unexpectedly"

    def jpeg(self, name):
        worker = self.workers.get(name)
        if worker is None:
            return None
        frame = worker.latest.get()
        if frame is None or time.time()-frame.timestamp > self.config.stale_seconds:
            return None
        detections = getattr(self, "detections", {}).get(name, [])
        image = annotate(frame.image, detections)
        width = min(self.config.preview_width or image.shape[1], image.shape[1])
        if width < image.shape[1]:
            image = cv2.resize(image, (width, round(image.shape[0]*width/image.shape[1])))
        ok, encoded = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, self.config.preview_jpeg_quality])
        return encoded.tobytes() if ok else None

    def _create_event(self, name, frame, detection, now):
        event_id = self.store.create(name, detection, now)
        filename = event_id+".jpg"
        if cv2.imwrite(str(self.store.media/filename), annotate(frame.image, [detection]), [cv2.IMWRITE_JPEG_QUALITY, self.config.evidence_jpeg_quality]):
            self.store.set_media(event_id, snapshot=filename)
        else:
            self.store.set_media(event_id, error="Snapshot write failed")
        self.pending.append({"id":event_id, "camera":name, "start":now-self.config.pre_seconds, "end":now+self.config.post_seconds, "frames":self.workers[name].evidence(now-self.config.pre_seconds, now), "last":now, "detection":detection})
        return event_id

    def _submit_clip(self, pending):
        # Bound in-flight encoding work; event rows report overload rather than queuing forever.
        self.media_jobs = [job for job in self.media_jobs if not job.done()]
        if len(self.media_jobs) >= 4:
            self.store.set_media(pending["id"], error="Evidence encoder busy; clip unavailable")
            return
        self.media_jobs.append(self.encoder.submit(self._write_clip, pending))

    def _write_clip(self, pending):
        try:
            result = clip.encode(pending["frames"], self.config.clip_fps, self.store.media, pending["id"], pending.get("detection"))
            logging.info("Event clip %s: %s, %d frames, encoded in %.0f ms", pending["id"], result.format, result.frames, result.encode_ms)
            self.clip_timings.append(result.encode_ms)
            if not self.store.set_media(pending["id"], clip=result.filename):
                (self.store.media/result.filename).unlink(missing_ok=True)
        except Exception as exc:
            logging.exception("Event evidence failed")
            self.store.set_media(pending["id"], error=str(exc))

    def _collect_evidence(self, now):
        for pending in list(self.pending):
            samples = self.workers[pending["camera"]].evidence(pending["last"]+1e-6, pending["end"])
            if samples:
                pending["frames"].extend(samples)
                pending["last"] = samples[-1][0]
            if now >= pending["end"]:
                self._submit_clip(pending)
                self.pending.remove(pending)

    def _run(self):
        due = {name:0.0 for name in self.workers}
        seen = {name:0 for name in self.workers}
        last_analysis = {}
        was_connected = {name:False for name in self.workers}
        self.detections = {}
        prune_at = time.monotonic()+60
        while not self.stop_event.is_set():
            for name, worker in self.workers.items():
                if self.stop_event.is_set():
                    break
                now = time.time()
                self.trackers[name].expire(now, self.store.close_event)
                frame = worker.latest.get()
                connected = frame is not None and now-frame.timestamp <= self.config.stale_seconds and worker.status()["connected"]
                if not connected:
                    self.trackers[name].rule.reset()
                    self.detections[name] = []
                    if was_connected[name]:
                        with self.lock:
                            self.metrics[name]["analysis_hz"] = 0.0
                    was_connected[name] = False
                    continue
                was_connected[name] = True
                if time.monotonic() < due[name] or frame.sequence == seen[name]:
                    continue
                # Start-to-start target; a slow model reduces measured rate without building a backlog.
                started = time.monotonic()
                due[name] = started+1/self.config.analysis_hz
                seen[name] = frame.sequence
                try:
                    if name in last_analysis and started-last_analysis[name] > self.config.alarm_gap_seconds:
                        self.trackers[name].rule.reset()
                    detections, timings = self.detector.predict(frame.image)
                    self.detections[name] = detections
                    self.trackers[name].update(detections, now, lambda d,t:self._create_event(name,frame,d,t), self.store.extend, self.store.close_event)
                    with self.lock:
                        self.metrics[name].update(timings)
                        self.metrics[name]["analyses"] += 1
                        self.metrics[name]["analysis_hz"] = 1/(started-last_analysis[name]) if name in last_analysis else 0
                        self.metrics[name]["pipeline_error"] = None
                    last_analysis[name] = started
                except Exception as exc:
                    logging.exception("Analysis failed for %s", name)
                    self.trackers[name].rule.reset()
                    self.detections[name] = []
                    with self.lock:
                        self.metrics[name]["pipeline_error"] = str(exc)
            self._collect_evidence(time.time())
            self.led.set_alarm(any(t.events for t in self.trackers.values()))
            if time.monotonic() >= prune_at:
                self._prune_retention()
                prune_at = time.monotonic()+60
            self.stop_event.wait(.02)
