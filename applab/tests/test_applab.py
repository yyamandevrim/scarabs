"""Packaging and adapter contracts; no board, network, or injected detections."""
import importlib.util
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace
import zipfile

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "station"))
from station.applab_link import AppLabLink
from station.mcu_bridge import make_link
from station.mcu_protocol import McuConfig


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def package(tmp_path_factory):
    builder = load("acorn_build", ROOT / "applab/build.py")
    builder.DIST = tmp_path_factory.mktemp("app-dist")
    app, archive = builder.build()
    # A rebuild must remove prior runtime state and all private additions.
    (app / "data").mkdir()
    (app / "data/panel-secret").write_text("PRIVATE_SENTINEL")
    (app / ".env").write_text("PRIVATE_SENTINEL")
    (app / ".DS_Store").write_text("PRIVATE_SENTINEL")
    builder.build()
    return app, archive


@pytest.fixture
def entry(package, monkeypatch):
    app, _ = package
    module = load("acorn_entry", ROOT / "applab/python/main.py")
    module.APP_ROOT = app
    monkeypatch.delenv("ACORN_PANEL_SECRET", raising=False)
    return module


def test_archive_structure_clean_and_full_source(package):
    app, archive = package
    with zipfile.ZipFile(archive) as z:
        names = z.namelist()
        assert "app.yaml" in names
        assert {"sketch/sketch.ino", "sketch/sketch.yaml", "python/main.py", "python/requirements.txt",
                "python/models/smoke.onnx", "python/station/static/index.html"} <= set(names)
        for name in names:
            assert not set(Path(name).parts) & {"data", "media", ".env", ".DS_Store", "__pycache__", ".cache"}
            assert ".local.toml" not in name
        assert b"PRIVATE_SENTINEL" not in z.read("python/main.py")
    for p in (ROOT / "station/station").rglob("*.py"):
        if "__pycache__" not in p.parts:
            assert p.read_bytes() == (app / "python/station" / p.relative_to(ROOT / "station/station")).read_bytes()
    for p in (ROOT / "firmware/acorn_mcu").glob("*.h"):
        assert p.read_bytes() == (app / "sketch" / p.name).read_bytes()
    manifest = json.loads((app / "BUILD.json").read_text())
    import hashlib
    for name, digest in manifest["files_sha256"].items():
        assert hashlib.sha256((app / name).read_bytes()).hexdigest() == digest
    import tomllib
    deps = tomllib.loads((ROOT / "station/pyproject.toml").read_text())["project"]["dependencies"]
    requirements = (app / "python/requirements.txt").read_text()
    assert all(dep in requirements for dep in deps)
    assert not any(line.startswith("opencv-python-headless") for line in requirements.splitlines())


def args(tmp_path, recorded=None):
    tmp_path.mkdir(exist_ok=True)
    secret = tmp_path / "panel-secret"
    secret.write_text("private-test-password-only")
    secret.chmod(0o600)
    return SimpleNamespace(data_dir=tmp_path, recorded=recorded)


def test_live_profile_and_no_camera_fallback(entry, tmp_path):
    options = args(tmp_path)
    with pytest.raises(ValueError, match="Map both cameras"):
        entry.station_config(options)
    settings = tmp_path / "settings.toml"
    settings.write_text('left="/dev/v4l/by-path/left-video-index0"\ncentre="/dev/v4l/by-path/centre-video-index0"\n')
    cfg = entry.station_config(options)
    assert (cfg.input_size, cfg.confidence, cfg.analysis_hz, cfg.similarity_iou, cfg.detector_view) == (192, .35, 1, .25, "center_crop")
    assert cfg.mcu.mode == "applab" and not cfg.lora.enabled
    assert [(c.width, c.height, c.capture_format, c.capture_fps) for c in cfg.cameras if c.active] == [(320, 240, "YUYV", 5)] * 2
    assert cfg.data_dir == tmp_path / "station"
    settings.write_text(settings.read_text() + 'profile="field"\nbridge="router"\n')
    field = entry.station_config(options)
    assert (field.input_size, field.confidence, field.analysis_hz, field.mcu.mode) == (640, .25, 1/6, "router")


def test_recorded_is_explicit_and_separate(entry, tmp_path, capsys):
    cfg = entry.station_config(args(tmp_path, recorded=tmp_path / "footage"))
    assert cfg.mcu.mode == "simulated" and cfg.data_dir == tmp_path / "recorded"
    assert all(c.kind == "file" for c in cfg.cameras if c.active)
    assert "Recorded demo" in capsys.readouterr().out


def test_password_fail_closed_private_and_never_overwrites(entry, tmp_path, monkeypatch, capsys):
    with pytest.raises(ValueError, match="password missing"):
        entry.read_secret(tmp_path)
    answers = iter(["a-strong-private-test-value"] * 2)
    monkeypatch.setattr(entry.getpass, "getpass", lambda _: next(answers))
    entry.set_password(tmp_path)
    assert entry.read_secret(tmp_path) == "a-strong-private-test-value"
    assert (tmp_path / "panel-secret").stat().st_mode & 0o777 == 0o600
    assert "a-strong-private-test-value" not in capsys.readouterr().out
    answers = iter(["another-private-test-value"] * 2)
    monkeypatch.setattr(entry.getpass, "getpass", lambda _: next(answers))
    with pytest.raises(FileExistsError):
        entry.set_password(tmp_path)
    (tmp_path / "panel-secret").chmod(0o644)
    with pytest.raises(ValueError, match="private"):
        entry.read_secret(tmp_path)


class FakeBridge:
    def __init__(self):
        self.handler = None
        self.failure = None
        self.calls = []
        self.registration_failure = False

    def provide(self, name, handler):
        if self.registration_failure:
            raise ConnectionError("router unavailable")
        assert name == "acorn_reading"
        self.handler = handler

    def call(self, *params, **kwargs):
        self.calls.append((params, kwargs))
        if self.failure:
            raise self.failure
        return 1

    def unprovide(self, name):
        assert name == "acorn_reading"
        self.handler = None


def test_applab_adapter_retries_calls_errors_and_shutdown():
    api = FakeBridge()
    api.registration_failure = True
    link = AppLabLink(.2, bridge=api, clock=lambda: 42)
    readings = []
    link.start(readings.append)
    assert "router unavailable" in link.status()["last_error"]
    api.registration_failure = False
    link.send_state(2, 7)
    assert api.calls == [(("acorn_state", 2, 7), {"timeout": .2})]
    api.handler(1, 2, 3)
    assert readings == [[1, 2, 3]]
    assert link.status()["mcu_acknowledged_at"] == 42
    assert link.status()["mcu_protocol"] == 1
    api.failure = TimeoutError("MCU missing")
    link.send_state(3, 8)
    assert link.status()["unanswered_requests"] == 1
    api.failure = None
    link.send_state(1, 9)
    assert link.status()["last_error"] is None
    saved_handler = api.handler
    link.stop()
    saved_handler(9)
    assert len(readings) == 1 and not link.status()["registered"]
    link.send_state(1, 10)
    assert len(api.calls) == 3
    assert isinstance(make_link(McuConfig(mode="applab")), AppLabLink)


def test_minimal_opencv_nms_matches_full_opencv(monkeypatch):
    import cv2
    import numpy as np
    from station.detector import nms_boxes
    native = cv2.dnn.NMSBoxes
    cases = [([], []), ([[0, 0, 10, 10]] * 3, [.35, .7, .7]),
             ([[0, 0, 10, 10], [20, 0, 10, 10]], [.9, .8])]
    rng = np.random.default_rng(7381)
    for _ in range(100):
        boxes = rng.uniform(0, 10, (30, 4)).tolist()
        scores = rng.uniform(0, 1, 30).tolist()
        cases.append((boxes, scores))
    expected = [np.asarray(native(boxes, scores, .35, .45)).reshape(-1).tolist() for boxes, scores in cases]
    monkeypatch.delattr(cv2, "dnn")
    assert [nms_boxes(boxes, scores, .35, .45) for boxes, scores in cases] == expected
