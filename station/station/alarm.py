"""Spatially consistent three-of-five votes, counted once per analysis."""
from collections import deque
from dataclasses import dataclass

@dataclass(frozen=True)
class Detection:
    box: tuple[float, float, float, float]  # Normalized xyxy in the original frame.
    confidence: float


def iou(a, b) -> float:
    intersection = max(0, min(a[2], b[2]) - max(a[0], b[0])) * max(0, min(a[3], b[3]) - max(a[1], b[1]))
    union = (a[2]-a[0])*(a[3]-a[1]) + (b[2]-b[0])*(b[3]-b[1]) - intersection
    return intersection / union if union > 0 else 0


class AlarmRule:
    def __init__(self, similarity_iou: float = .25):
        self.threshold = similarity_iou
        self.history = deque(maxlen=5)

    def reset(self):
        self.history.clear()

    def observe(self, detections: list[Detection]) -> list[Detection]:
        self.history.append(detections)
        # Each candidate must be present now. Multiple boxes in one frame count as one vote.
        return [d for d in detections if sum(any(iou(d.box, p.box) >= self.threshold for p in frame) for frame in self.history) >= 3]


@dataclass
class OpenEvent:
    id: str
    detection: Detection
    last_seen: float


class EventTracker:
    def __init__(self, similarity_iou: float, timeout: float, history_gap: float | None = None):
        self.rule = AlarmRule(similarity_iou)
        self.timeout = timeout
        self.history_gap = history_gap
        self.last_analysis = None
        self.events: list[OpenEvent] = []

    def update(self, detections, now, create, extend, close):
        if self.history_gap is not None and self.last_analysis is not None and now-self.last_analysis > self.history_gap:
            self.rule.reset()
        self.last_analysis = now
        for event in list(self.events):
            if now - event.last_seen > self.timeout:
                close(event.id, now)
                self.events.remove(event)
        candidates = self.rule.observe(detections)
        matched = set()
        for detection in sorted(detections, key=lambda d: d.confidence, reverse=True):
            event = next((e for e in self.events if iou(e.detection.box, detection.box) >= self.rule.threshold), None)
            if event:
                if event.id not in matched:
                    extend(event.id, detection, now)
                    event.detection, event.last_seen = detection, now
                    matched.add(event.id)
            elif detection in candidates:
                event = OpenEvent(create(detection, now), detection, now)
                self.events.append(event)
                matched.add(event.id)
