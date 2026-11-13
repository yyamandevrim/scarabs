"""Independent capture workers: one latest frame, bounded compressed evidence ring."""
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from threading import Event, Lock, Thread
import time
import cv2

@dataclass(frozen=True)
class Frame:
    sequence: int
    timestamp: float
    image: object

class LatestFrame:
    def __init__(self):
        self.lock = Lock()
        self.value = None
        self.sequence = 0

    def put(self, image, timestamp):
        with self.lock:
            self.sequence += 1
            self.value = Frame(self.sequence, timestamp, image)

    def get(self):
        with self.lock:
            return self.value

    def clear(self):
        with self.lock:
            self.value = None

class CaptureWorker:
    def __init__(self, camera, config, factory=None):
        self.camera, self.config = camera, config
        self.latest = LatestFrame()
        self.stop_event = Event()
        self.thread = None
        self.lock = Lock()
        self.connected = False
        self.error = "Waiting for first frame"
        self.capture_fps = 0.0
        self.last_frame_at = None
        # No raw-frame queue. This ring is compressed and used only for event evidence.
        self.ring = deque(maxlen=max(2, int((config.pre_seconds+config.post_seconds+2)*config.clip_fps)+2))
        self.factory = factory or self._open
        # A source path that vanishes while running (file removed/renamed, USB
        # by-path/by-id link gone on unplug) is reported as lost within this interval.
        self.watched = Path(camera.source) if factory is None else None
        self.watch_interval = .5

    def _open(self):
        if self.camera.kind == "usb":
            cap = cv2.VideoCapture(self.camera.source, cv2.CAP_V4L2)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.camera.width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.camera.height)
            return cap
        return cv2.VideoCapture(self.camera.source)

    def status(self):
        with self.lock:
            return {"connected": self.connected, "error": self.error, "capture_fps": self.capture_fps, "last_frame_at": self.last_frame_at}

    def evidence(self, start, end):
        with self.lock:
            return [(t, data) for t, data in self.ring if start <= t <= end]

    def start(self):
        if not self.camera.active:
            return
        self.thread = Thread(target=self._run, name=f"capture-{self.camera.name}", daemon=True)
        self.thread.start()

    def stop(self):
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=4)

    def _lost(self, reason):
        self.latest.clear()
        with self.lock:
            self.connected = False
            self.error = reason
            self.capture_fps = 0
            self.ring.clear()

    def _run(self):
        while not self.stop_event.is_set():
            cap = None
            try:
                cap = self.factory()
                if not cap.isOpened():
                    raise OSError("Cannot open source")
                fps = cap.get(cv2.CAP_PROP_FPS)
                fps = fps if 0 < fps <= 120 else 25
                next_frame = time.monotonic()
                last_sample, previous = 0.0, None
                next_check = time.monotonic()+self.watch_interval
                while not self.stop_event.is_set():
                    if self.watched is not None and time.monotonic() >= next_check:
                        next_check = time.monotonic()+self.watch_interval
                        if not self.watched.exists():
                            raise OSError("Source path disappeared (file removed or device unplugged)")
                    ok, image = cap.read()
                    if not ok:
                        if self.camera.kind == "file" and self.camera.loop:
                            # Reopen by path instead of seeking the open handle, so a file
                            # that was removed or replaced is noticed at the loop point too.
                            cap.release()
                            cap = self.factory()
                            if not cap.isOpened():
                                raise OSError("Cannot reopen source at loop restart")
                            ok, image = cap.read()
                        if not ok:
                            raise OSError("Source disconnected or end of unreadable clip")
                    now = time.time()
                    image = cv2.resize(image, (self.camera.width, self.camera.height))
                    self.latest.put(image, now)
                    jpeg = None
                    if now-last_sample >= 1/self.config.clip_fps:
                        small = cv2.resize(image, (self.config.clip_width, max(2, round(image.shape[0]*self.config.clip_width/image.shape[1]))))
                        ok, encoded = cv2.imencode(".jpg", small, [cv2.IMWRITE_JPEG_QUALITY, 75])
                        if ok:
                            jpeg = encoded.tobytes()
                        last_sample = now
                    with self.lock:
                        self.connected, self.error, self.last_frame_at = True, None, now
                        if previous is not None and now > previous:
                            instant = 1/(now-previous)
                            self.capture_fps = instant if not self.capture_fps else .9*self.capture_fps+.1*instant
                        if jpeg:
                            self.ring.append((now, jpeg))
                    previous = now
                    # Files play in wall-clock time; USB read() already waits for its next frame.
                    if self.camera.kind == "file":
                        next_frame += 1/fps
                        self.stop_event.wait(max(0, next_frame-time.monotonic()))
            except Exception as exc:
                self._lost(str(exc))
            finally:
                if cap is not None:
                    cap.release()
            self.stop_event.wait(self.config.retry_seconds)
        self._lost("Stopped")
