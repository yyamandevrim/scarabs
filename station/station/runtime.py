"""One shared detector, round-robin analysis, independent capture and local evidence."""
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from pathlib import Path
from threading import Event, Lock, Thread
import logging
import time
import cv2
from . import clip
from .alarm import EventTracker
from .capture import CaptureWorker
from .detector import SmokeDetector, annotate
from .led import LedHook
from .storage import EventStore

class Station:
    def __init__(self, config, detector=None, capture_factory=None):
        self.config = config
        self.detector = detector if detector is not None else SmokeDetector(config.model, config.input_size, config.confidence, config.nms_iou, config.ort_threads)
        self.store = EventStore(config.data_dir)
        self.workers = {c.name: CaptureWorker(c, config, factory=(lambda c=c: capture_factory(c)) if capture_factory else None) for c in config.cameras if c.active}
        self.trackers = {name: EventTracker(config.similarity_iou, config.event_timeout) for name in self.workers}
        self.led = LedHook(config.led_path)
        self.stop_event = Event()
        self.lock = Lock()
        self.metrics = {name: {"analyses":0, "preprocess_ms":None, "inference_ms":None, "analysis_ms":None, "analysis_hz":0.0, "pipeline_error":None} for name in self.workers}
        self.pending = []
        self.media_jobs = []
        self.encoder = ThreadPoolExecutor(max_workers=1, thread_name_prefix="evidence", initializer=clip.lower_thread_priority)
        self.clip_timings = deque(maxlen=50)
        self.thread = None

    def start(self):
        self.store.close_previous(time.time())
        self.store.prune(time.time(), self.config.retention_days)
        for worker in self.workers.values():
            worker.start()
        self.thread = Thread(target=self._run, name="shared-detector", daemon=True)
        self.thread.start()

    def stop(self):
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=30)
        for worker in self.workers.values():
            worker.stop()
        for pending in self.pending:
            self._submit_clip(pending)
        self.pending.clear()
        self.encoder.shutdown(wait=True)
        now = time.time()
        for tracker in self.trackers.values():
            for event in tracker.events:
                self.store.close_event(event.id, now)
        self.led.set_alarm(False)

    def status(self):
        now = time.time()
        cameras = []
        for camera in self.config.cameras:
            item = asdict(camera)
            item.pop("source")  # Do not expose host paths in the panel.
            if not camera.active:
                item.update(status="inactive", status_text="takılı, bağlı değil", connected=False)
            else:
                state = self.workers[camera.name].status()
                connected = state["connected"] and state["last_frame_at"] is not None and now-state["last_frame_at"] <= self.config.stale_seconds
                with self.lock:
                    item.update(self.metrics[camera.name])
                item.update(state)
                item.update(connected=connected, status="connected" if connected else "disconnected", status_text="bağlı" if connected else "bağlantı koptu")
            cameras.append(item)
        return {"cameras": cameras, "target_analysis_hz":self.config.analysis_hz, "input_size":self.config.input_size, "confidence_threshold":self.config.confidence, "offline":True}

    def jpeg(self, name):
        worker = self.workers.get(name)
        if worker is None:
            return None
        frame = worker.latest.get()
        if frame is None or time.time()-frame.timestamp > self.config.stale_seconds:
            return None
        detections = getattr(self, "detections", {}).get(name, [])
        image = annotate(frame.image, detections)
        width = min(960, image.shape[1])
        image = cv2.resize(image, (width, round(image.shape[0]*width/image.shape[1])))
        ok, encoded = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, 80])
        return encoded.tobytes() if ok else None

    def _create_event(self, name, frame, detection, now):
        event_id = self.store.create(name, detection, now)
        filename = event_id+".jpg"
        if cv2.imwrite(str(self.store.media/filename), annotate(frame.image, [detection])):
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
                frame = worker.latest.get()
                connected = frame is not None and now-frame.timestamp <= self.config.stale_seconds and worker.status()["connected"]
                if not connected:
                    self.trackers[name].rule.reset()
                    self.detections[name] = []
                    if was_connected[name]:
                        with self.lock:
                            self.metrics[name]["analysis_hz"] = 0.0
                    was_connected[name] = False
                    self.trackers[name].update([],now,lambda *args:None,self.store.extend,self.store.close_event)
                    continue
                was_connected[name] = True
                if time.monotonic() < due[name] or frame.sequence == seen[name]:
                    continue
                # Start-to-start target; a slow model reduces measured rate without building a backlog.
                started = time.monotonic()
                due[name] = started+1/self.config.analysis_hz
                seen[name] = frame.sequence
                try:
                    if name in last_analysis and started-last_analysis[name] > max(self.config.stale_seconds, 2/self.config.analysis_hz):
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
                    with self.lock:
                        self.metrics[name]["pipeline_error"] = str(exc)
            self._collect_evidence(time.time())
            self.led.set_alarm(any(t.events for t in self.trackers.values()))
            if time.monotonic() >= prune_at:
                self.store.prune(time.time(), self.config.retention_days)
                prune_at = time.monotonic()+60
            self.stop_event.wait(.02)
