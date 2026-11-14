"""Independent capture workers: one latest frame, bounded compressed evidence ring."""
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from threading import Event, Lock, Thread
import time
import cv2
import numpy as np


def validate_frame(image):
    """Reject malformed frames and the observed zero-filled YUV corruption.

    OpenCV can return success with a full-sized BGR array even when UVC supplied
    too little YUYV data. Zero-filled Y/U/V becomes a flat (0, 154, 0) footer.
    This signature check supplements shape validation; it is not a universal
    image-integrity test. Run before publishing to analysis or evidence.
    """
    if image is None or image.ndim != 3 or image.shape[2] != 3 or min(image.shape[:2]) < 2 or image.dtype != np.uint8:
        raise OSError("Invalid camera frame shape or pixel type")
    footer = image[-max(2, image.shape[0]//4):, ::4]
    green_padding = ((footer[:, :, 0] <= 3) & (footer[:, :, 2] <= 3)
                     & (footer[:, :, 1] >= 145) & (footer[:, :, 1] <= 165))
    if np.mean(green_padding) > .98:
        raise OSError("Invalid/truncated camera frame: zero-filled YUV footer")

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
        self.capture_width = self.capture_height = 0
        self.capture_format = None
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
            if self.camera.capture_format:
                cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*self.camera.capture_format))
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.camera.width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.camera.height)
            if self.camera.capture_fps:
                cap.set(cv2.CAP_PROP_FPS, self.camera.capture_fps)
            return cap
        return cv2.VideoCapture(self.camera.source)

    def status(self):
        with self.lock:
            return {"connected": self.connected, "error": self.error, "capture_fps": self.capture_fps, "last_frame_at": self.last_frame_at,
                    "capture_width": self.capture_width, "capture_height": self.capture_height, "capture_format": self.capture_format}

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
                fourcc = int(cap.get(cv2.CAP_PROP_FOURCC))
                capture_format = ''.join(chr((fourcc >> (8*i)) & 255) for i in range(4)).rstrip('\x00')
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
                    validate_frame(image)
                    now = time.time()
                    # Preserve actual USB pixels: a driver's fallback must not be
                    # enlarged to the requested size or distorted to another aspect ratio.
                    if self.camera.kind == "file":
                        image = cv2.resize(image, (self.camera.width, self.camera.height))
                    self.latest.put(image, now)
                    jpeg = None
                    if now-last_sample >= 1/self.config.clip_fps:
                        width = min(self.config.clip_width, image.shape[1])
                        small = image if width == image.shape[1] else cv2.resize(image, (width, max(2, round(image.shape[0]*width/image.shape[1]))))
                        ok, encoded = cv2.imencode(".jpg", small, [cv2.IMWRITE_JPEG_QUALITY, self.config.evidence_jpeg_quality])
                        if ok:
                            jpeg = encoded.tobytes()
                        last_sample = now
                    with self.lock:
                        self.connected, self.error, self.last_frame_at = True, None, now
                        self.capture_height, self.capture_width = image.shape[:2]
                        self.capture_format = capture_format
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
