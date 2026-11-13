"""Event clip encoding: browser-playable WebM/VP8 first, MJPEG AVI as the last resort.

The pip OpenCV wheels bundle FFmpeg with libvpx on both macOS ARM64 and Linux
ARM64, so VP8 needs no system ffmpeg binary. The Linux ARM64 wheel has no H.264
software encoder, which is why H.264/MP4 is not the primary format. OpenCV's
built-in MJPEG AVI writer needs no FFmpeg at all and stays as the fallback.
"""
from dataclasses import dataclass
import logging
import os
import sys
import threading
import time
import cv2
import numpy as np
from .detector import annotate

@dataclass(frozen=True)
class ClipFormat:
    suffix: str
    fourcc: str
    api: int
    name: str

# Order matters: the first format whose writer opens and whose output decodes wins.
FORMATS = (
    ClipFormat(".webm", "VP80", cv2.CAP_FFMPEG, "WebM/VP8"),
    ClipFormat(".avi", "MJPG", cv2.CAP_ANY, "MJPEG AVI"),
)
BROWSER_PLAYABLE = (".webm",)


@dataclass(frozen=True)
class ClipResult:
    filename: str
    format: str
    frames: int
    encode_ms: float


def lower_thread_priority():
    """Keep the encoder behind capture/inference on Linux (per-thread nice)."""
    if sys.platform.startswith("linux"):
        try:
            os.setpriority(os.PRIO_PROCESS, threading.get_native_id(), 10)
        except OSError:
            logging.warning("Could not lower evidence encoder priority")


def resample(frames, fps):
    """Pick ring samples at a fixed rate by capture timestamp; never speeds up gaps."""
    times = np.arange(frames[0][0], frames[-1][0]+.5/fps, 1/fps)
    index = 0
    for timestamp in times:
        while index+1 < len(frames) and frames[index+1][0] <= timestamp:
            index += 1
        yield frames[index][1]


def _decodes(path):
    cap = cv2.VideoCapture(str(path))
    try:
        return cap.isOpened() and cap.read()[0]
    finally:
        cap.release()


def _write(path, fmt, frames, fps, detection):
    first = cv2.imdecode(np.frombuffer(frames[0][1], np.uint8), cv2.IMREAD_COLOR)
    height, width = first.shape[:2]
    writer = cv2.VideoWriter(str(path), fmt.api, cv2.VideoWriter_fourcc(*fmt.fourcc), fps, (width, height))
    count = 0
    try:
        if not writer.isOpened():
            return 0
        for data in resample(frames, fps):
            image = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
            if image is None or image.shape[:2] != (height, width):
                continue
            # Same amber box and label as the snapshot: the opening detection.
            writer.write(annotate(image, [detection]) if detection is not None else image)
            count += 1
    finally:
        writer.release()
    return count


def encode(frames, fps, media_dir, event_id, detection=None, formats=None):
    """Write the first working format; return ClipResult or raise OSError if none works."""
    if not frames:
        raise OSError("No captured evidence frames")
    failures = []
    started = time.perf_counter()
    for fmt in formats or FORMATS:
        temporary = media_dir/(event_id+".tmp"+fmt.suffix)
        try:
            count = _write(temporary, fmt, frames, fps, detection)
            if count and temporary.is_file() and temporary.stat().st_size and _decodes(temporary):
                final = media_dir/(event_id+fmt.suffix)
                temporary.replace(final)
                elapsed = (time.perf_counter()-started)*1000
                return ClipResult(final.name, fmt.name, count, elapsed)
            failures.append(f"{fmt.name} encoder unavailable")
        except Exception as exc:
            failures.append(f"{fmt.name}: {exc}")
        temporary.unlink(missing_ok=True)
        logging.warning("Event clip format %s failed; trying next", fmt.name)
    raise OSError("; ".join(failures))
