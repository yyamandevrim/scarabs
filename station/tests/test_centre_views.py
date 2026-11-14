"""Centre views change which pixels are analysed, never scores or alarm voting."""
from pathlib import Path
from types import SimpleNamespace

import cv2
import numpy as np
import pytest

from station import detector as module
from station.alarm import AlarmRule, Detection
from station.centre_views import CentreViewsDetector, build_detector, centre_square
from station.detector import SmokeDetector

ROOT = Path(__file__).resolve().parents[1]


class Session:
    """One box in the middle of every input, at the score set on the class."""
    score = .8

    def __init__(self, *args, **kwargs):
        self.tensors = []

    def get_inputs(self):
        return [SimpleNamespace(name="images", shape=[1, 3, "h", "w"])]

    def get_modelmeta(self):
        return SimpleNamespace(custom_metadata_map={"names": "{0: 'smoke'}"})

    def run(self, _, inputs):
        self.tensors.append(inputs["images"])
        return [np.array([[[96], [96], [96], [96], [self.score]]], np.float32)]


@pytest.fixture
def inner(tmp_path, monkeypatch):
    model = tmp_path / "model.onnx"
    model.touch()
    monkeypatch.setattr(module.ort, "InferenceSession", Session)
    return lambda **kw: SmokeDetector(model, input_size=192, **kw)


def tensor_of(pixels):
    return np.ascontiguousarray(pixels[:, :, ::-1].transpose(2, 0, 1)[None], dtype=np.float32) / 255


def test_centre_square_offsets_and_clamp():
    frame = np.zeros((240, 320, 3), np.uint8)
    crop, x, y = centre_square(frame, 192)
    assert crop.shape == (192, 192, 3) and (x, y) == (64, 24)
    crop, x, y = centre_square(frame, 500)
    assert crop.shape == (240, 240, 3) and (x, y) == (40, 0)


def test_native_view_feeds_untouched_camera_pixels_and_maps_boxes(inner):
    frame = np.random.default_rng(3).integers(0, 256, (240, 320, 3), dtype=np.uint8)
    original = frame.copy()
    detector = CentreViewsDetector(inner(), sides=(192,))
    detections, timings = detector.predict(frame)
    session = detector.detector.session
    assert len(session.tensors) == 1
    # No resampling and no padding: the tensor is exactly the centred camera pixels.
    np.testing.assert_array_equal(session.tensors[0], tensor_of(original[24:216, 64:256]))
    np.testing.assert_array_equal(frame, original)
    # Model box 48..144 of 192 inside the crop at (64, 24), in full-frame coordinates.
    assert detections == [Detection(pytest.approx((112/320, 72/240, 208/320, 168/240)), pytest.approx(.8))]
    assert set(timings) == {"preprocess_ms", "inference_ms", "analysis_ms"}
    assert all(value >= 0 for value in timings.values())


def test_two_views_run_two_inferences_and_merge_one_plume(inner):
    frame = np.random.default_rng(4).integers(0, 256, (240, 320, 3), dtype=np.uint8)
    detector = CentreViewsDetector(inner())
    detections, _ = detector.predict(frame)
    tensors = detector.detector.session.tensors
    assert len(tensors) == 2
    np.testing.assert_array_equal(tensors[0], tensor_of(frame[24:216, 64:256]))
    np.testing.assert_array_equal(tensors[1], tensor_of(cv2.resize(frame[40:200, 80:240], (192, 192))))
    # Concentric boxes of the same plume overlap above the NMS IoU: one candidate.
    assert len(detections) == 1
    assert detections[0].confidence == pytest.approx(.8)


def test_small_frame_clamps_views_to_one_inference(inner):
    frame = np.zeros((120, 160, 3), np.uint8)
    detector = CentreViewsDetector(inner())
    detections, _ = detector.predict(frame)
    assert len(detector.detector.session.tensors) == 1
    assert detections[0].box == pytest.approx((50/160, 30/120, 110/160, 90/120))


def test_views_keep_confidence_gate_and_three_of_five(inner):
    frame = np.zeros((240, 320, 3), np.uint8)
    # A score under the gate stays under it in every view.
    assert CentreViewsDetector(inner(confidence=.9)).predict(frame)[0] == []
    detector = CentreViewsDetector(inner(confidence=.35))
    assert detector.confidence == .35 and detector.size == 192
    rule = AlarmRule()
    detections, _ = detector.predict(frame)
    assert not rule.observe(detections)
    assert not rule.observe([])
    assert not rule.observe(detections)
    assert not rule.observe([])
    assert rule.observe(detections) == detections


def test_rejects_unusable_sides(inner):
    for sides in ((), (16,), (192.5,)):
        with pytest.raises(ValueError, match="centre view sides"):
            CentreViewsDetector(inner(), sides=sides)


def test_build_detector_wraps_only_the_centre_zoom_view(tmp_path, monkeypatch):
    model = tmp_path / "model.onnx"
    model.touch()
    monkeypatch.setattr(module.ort, "InferenceSession", Session)
    config = SimpleNamespace(model=model, input_size=192, confidence=.35, nms_iou=.45, ort_threads=2, detector_view="centre_zoom")
    zoom = build_detector(config)
    assert isinstance(zoom, CentreViewsDetector) and zoom.sides == (192, 160)
    assert zoom.detector.view == "full" and zoom.confidence == .35 and zoom.nms_iou == .45
    for view in ("full", "center_crop"):
        config.detector_view = view
        plain = build_detector(config)
        assert type(plain) is SmokeDetector and plain.view == view


def test_real_model_project_clips_through_centre_views():
    """Licensed clips at the board's 320x240: smoke opens a vote, negatives never score."""
    model = ROOT / "models/smoke.onnx"
    clips = {name: ROOT / "media" / name for name in ("smoke.ogv", "fog.webm", "cloud.webm", "glare.webm")}
    if not model.is_file() or not all(path.is_file() for path in clips.values()):
        pytest.skip("Run fetch_model.py and fetch_footage.py before real-clip view tests")
    detector = CentreViewsDetector(SmokeDetector(model, input_size=192, confidence=.35))
    alarms = {}
    for name, path in clips.items():
        capture, rule, hits, alarmed, index = cv2.VideoCapture(str(path)), AlarmRule(), 0, 0, 0
        while True:
            ok, frame = capture.read()
            if not ok:
                break
            if index % 25 == 0:
                detections, _ = detector.predict(cv2.resize(frame, (320, 240)))
                hits += bool(detections)
                alarmed += bool(rule.observe(detections))
            index += 1
        capture.release()
        alarms[name] = (hits, alarmed)
    assert alarms["smoke.ogv"][1] > 0
    assert all(alarms[name] == (0, 0) for name in ("fog.webm", "cloud.webm", "glare.webm")), alarms


def test_config_accepts_centre_zoom_and_station_runs_it(config, monkeypatch):
    from dataclasses import replace
    from station.runtime import Station
    monkeypatch.setattr(module.ort, "InferenceSession", Session)
    monkeypatch.setattr(Path, "is_file", lambda self: True)
    cfg = replace(config, detector_view="centre_zoom", input_size=192)
    station = Station(cfg)
    try:
        assert isinstance(station.detector, CentreViewsDetector)
        assert station.detector.detector.view == "full"
        assert station.status()["analysis_profile"]["detector_view"] == "centre_zoom"
    finally:
        station.stop()


def test_centre_zoom_boxes_stay_inside_the_analysed_square(inner, monkeypatch):
    """Oversized model boxes must map back inside the largest crop, never past the frame."""
    monkeypatch.setattr(Session, "run", lambda self, _, inputs: [np.array([[[96], [96], [400], [400], [.8]]], np.float32)])
    detections, _ = CentreViewsDetector(inner()).predict(np.zeros((240, 320, 3), np.uint8))
    assert detections
    for d in detections:
        assert 64/320 - 1e-9 <= d.box[0] < d.box[2] <= 256/320 + 1e-9
        assert 24/240 - 1e-9 <= d.box[1] < d.box[3] <= 216/240 + 1e-9
