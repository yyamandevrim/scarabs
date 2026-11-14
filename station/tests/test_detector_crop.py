"""The optional crop changes pixels/FOV, never confidence or alarm voting."""
from types import SimpleNamespace
from dataclasses import replace

import cv2
import numpy as np
import pytest

from station import detector as module
from station.alarm import AlarmRule
from station.detector import SmokeDetector
from station.runtime import Station


class Session:
    def __init__(self, *args, **kwargs):
        self.calls = 0

    def get_inputs(self):
        return [SimpleNamespace(name="images", shape=[1, 3, "h", "w"])]

    def get_modelmeta(self):
        return SimpleNamespace(custom_metadata_map={"names": "{0: 'smoke'}"})

    def run(self, _, inputs):
        self.calls += 1
        self.tensor = inputs["images"]
        # Central half-width box at model input 192.
        return [np.array([[[96], [96], [96], [96], [.8]]], np.float32)]


@pytest.fixture
def make_detector(tmp_path, monkeypatch):
    model = tmp_path / "model.onnx"
    model.touch()
    monkeypatch.setattr(module.ort, "InferenceSession", Session)
    return lambda **kw: SmokeDetector(model, input_size=192, **kw)


@pytest.mark.parametrize("shape,expected", [
    ((240, 320), (.3125, .25, .6875, .75)),
    ((320, 240), (.25, .3125, .75, .6875)),
    ((241, 322), (100.25/322, .25, 220.75/322, .75)),
])
def test_crop_pixels_coordinates_and_single_inference(make_detector, shape, expected):
    h, w = shape
    frame = np.random.default_rng(7).integers(0, 256, (h, w, 3), dtype=np.uint8)
    original = frame.copy()
    detector = make_detector(view="center_crop")
    detections, timing = detector.predict(frame)
    assert len(detections) == 1
    assert detections[0].box == pytest.approx(expected)
    assert detector.session.calls == 1
    side = min(h, w)
    x, y = (w-side)//2, (h-side)//2
    pixels = cv2.resize(original[y:y+side, x:x+side], (192, 192))
    tensor = np.ascontiguousarray(pixels[:, :, ::-1].transpose(2, 0, 1)[None], dtype=np.float32)/255
    np.testing.assert_array_equal(detector.session.tensor, tensor)
    np.testing.assert_array_equal(frame, original)
    assert all(t >= 0 for t in timing.values())


def test_square_crop_is_identical_to_full_frame(make_detector):
    frame = np.random.default_rng(8).integers(0, 256, (241, 241, 3), dtype=np.uint8)
    full, crop = make_detector(), make_detector(view="center_crop")
    assert full.predict(frame)[0] == crop.predict(frame)[0]
    np.testing.assert_array_equal(full.session.tensor, crop.session.tensor)


def test_crop_keeps_confidence_gate_and_three_of_five(make_detector):
    frame = np.zeros((240, 320, 3), np.uint8)
    detector = make_detector(view="center_crop", confidence=.35)
    rule = AlarmRule()
    detections, _ = detector.predict(frame)
    assert not rule.observe(detections)
    assert not rule.observe([])
    assert not rule.observe(detections)
    assert not rule.observe([])
    assert rule.observe(detections) == detections
    assert make_detector(view="center_crop", confidence=.9).predict(frame)[0] == []


def test_crop_boxes_clip_to_observed_region(make_detector, monkeypatch):
    def oversized(self, _, inputs):
        return [np.array([[[96], [96], [384], [384], [.8]]], np.float32)]
    monkeypatch.setattr(Session, "run", oversized)
    detector = make_detector(view="center_crop")
    box = detector.predict(np.zeros((240, 320, 3), np.uint8))[0][0].box
    assert box == pytest.approx((.125, 0, .875, 1))


def test_unknown_view_rejected(make_detector):
    with pytest.raises(ValueError, match="view"):
        make_detector(view="unknown")


def test_config_defaults_opt_in_and_runtime_wiring(config, monkeypatch):
    assert config.detector_view == "full"
    with pytest.raises(ValueError, match="detector_view"):
        replace(config, detector_view="unknown")
    cfg = replace(config, detector_view="center_crop")
    calls = []
    def create(*args, **kwargs):
        calls.append(kwargs)
        return object()
    monkeypatch.setattr("station.runtime.SmokeDetector", create)
    station = Station(cfg)
    try:
        assert calls == [{"view": "center_crop"}]
        assert station.status()["analysis_profile"]["detector_view"] == "center_crop"
    finally:
        station.stop()
