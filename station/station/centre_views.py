"""Optional centre-zoom analysis for a low-resolution camera (demo profile).

Letterboxing a 320x240 frame into a 192 input shrinks and resamples the scene
and spends a quarter of the input on padding. This wrapper instead hands the
model centred square crops of the frame, by default 192 px (native camera
pixels at input 192) and 160 px (a 1.2x zoom), and merges the boxes with the
detector's own NMS. One inference per crop.

It changes only which pixels are analysed. Pixel values, the confidence gate,
NMS IoU and the three-of-five spatial vote are untouched, and the frame border
outside the largest crop is not analysed (a narrower field of view).

Measured 2026-11-14 on saved board frames (320x240, input 192, gate 0.35):
``media/smoke.ogv`` on a screen 0/89 frames letterboxed, 39/89 here; fog, cloud,
glare, hall and fireplace frames opened no three-of-five vote either way.
"""
from time import perf_counter
import cv2
import numpy as np
from .alarm import Detection
from .detector import SmokeDetector

DEFAULT_SIDES = (192, 160)
VIEW = "centre_zoom"  # Value of ``detector_view`` that selects this wrapper.


def build_detector(config, factory=SmokeDetector):
    """The detector a configuration asks for; other views pass straight through."""
    zoom = config.detector_view == VIEW
    detector = factory(config.model, config.input_size, config.confidence, config.nms_iou, config.ort_threads,
                       view="full" if zoom else config.detector_view)
    return CentreViewsDetector(detector) if zoom else detector


def centre_square(frame, side):
    """Centred square of at most ``side`` pixels, with its top-left offset."""
    h, w = frame.shape[:2]
    side = min(side, h, w)
    x, y = (w - side) // 2, (h - side) // 2
    return frame[y:y + side, x:x + side], x, y


class CentreViewsDetector:
    """Wraps a ``SmokeDetector``; same ``predict`` contract, full-frame boxes."""

    def __init__(self, detector, sides=DEFAULT_SIDES):
        if not sides or any(not isinstance(side, int) or side < 32 for side in sides):
            raise ValueError("centre view sides must be integers of at least 32 pixels")
        self.detector = detector
        self.sides = tuple(sides)

    def __getattr__(self, name):
        # Thresholds, input size and session stay those of the wrapped detector.
        return getattr(self.detector, name)

    def predict(self, frame):
        start = perf_counter()
        fh, fw = frame.shape[:2]
        detections, timings, seen = [], {"preprocess_ms": 0.0, "inference_ms": 0.0}, set()
        for side in self.sides:
            crop, x, y = centre_square(frame, side)
            side = crop.shape[0]
            if side in seen:  # A small frame clamps several views to one square.
                continue
            seen.add(side)
            found, timing = self.detector.predict(crop)
            for key in timings:
                timings[key] += timing[key]
            detections += [Detection(((x + d.box[0] * side) / fw, (y + d.box[1] * side) / fh,
                                      (x + d.box[2] * side) / fw, (y + d.box[3] * side) / fh), d.confidence)
                           for d in found]
        if len(seen) > 1 and len(detections) > 1:
            # The same plume seen in two crops is one candidate.
            boxes = [[d.box[0] * fw, d.box[1] * fh, (d.box[2] - d.box[0]) * fw, (d.box[3] - d.box[1]) * fh] for d in detections]
            keep = cv2.dnn.NMSBoxes(boxes, [d.confidence for d in detections], self.detector.confidence, self.detector.nms_iou)
            detections = [detections[i] for i in np.asarray(keep).reshape(-1)]
        timings["analysis_ms"] = (perf_counter() - start) * 1000
        return detections, timings
