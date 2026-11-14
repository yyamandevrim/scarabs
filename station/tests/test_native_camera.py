"""Platform routing without opening hardware; Linux negotiation must stay intact."""
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
import time

import cv2
import numpy as np
import pytest
from station import capture, config as configuration
from station.config import load_config
from conftest import ROOT, wait_until


def platform(monkeypatch, name):
    # Replace only the modules' platform view, never pytest's global sys module.
    for module in (configuration, capture):
        monkeypatch.setattr(module, 'sys', SimpleNamespace(platform=name), raising=False)


@pytest.mark.parametrize('source', ['0', '2'])
def test_native_mac_index_config_keeps_index_instead_of_resolving_a_path(config, monkeypatch, tmp_path, source):
    platform(monkeypatch, 'darwin')
    path = tmp_path / 'mac.toml'
    path.write_text(f'''[cameras.left]
kind = "avfoundation"
source = "{source}"
[cameras.centre]
active = false
source = "media/cloud.webm"
[cameras.right]
active = false
source = "media/cloud.webm"
''')
    loaded = load_config(path)
    assert loaded.cameras[0].source == source
    assert loaded.cameras[1].source == str(tmp_path / 'media/cloud.webm')


@pytest.mark.parametrize('source', ['-1', '+1', ' 0', '0.0', 'camera', '/dev/video0', '０', '2147483648'])
def test_native_mac_source_requires_a_nonnegative_opencv_index(config, monkeypatch, source):
    platform(monkeypatch, 'darwin')
    cameras = [replace(c, kind='avfoundation', source=source) if c.name == 'left' else c for c in config.cameras]
    with pytest.raises(ValueError, match='AVFoundation.*index'):
        replace(config, cameras=cameras)


@pytest.mark.parametrize('host', ['linux', 'win32'])
def test_native_mac_source_is_rejected_on_other_platforms(config, monkeypatch, host):
    platform(monkeypatch, host)
    cameras = [replace(c, kind='avfoundation', source='0') if c.name == 'left' else c for c in config.cameras]
    with pytest.raises(ValueError, match='AVFoundation.*macOS'):
        replace(config, cameras=cameras)


class Camera:
    def __init__(self):
        self.settings = []
        self.released = False

    def set(self, key, value):
        self.settings.append((key, value))
        return False  # Driver may decline a requested size/rate.

    def get(self, key):
        return {cv2.CAP_PROP_FPS: 30, cv2.CAP_PROP_FOURCC: 0}.get(key, 0)

    def isOpened(self):
        return True

    def read(self):
        time.sleep(.01)
        return True, np.full((480, 640, 3), 80, np.uint8)

    def release(self):
        self.released = True


def test_mac_capture_uses_avfoundation_without_filesystem_watch_or_resizing(config, monkeypatch):
    platform(monkeypatch, 'darwin')
    opened, device = [], Camera()
    monkeypatch.setattr(cv2, 'VideoCapture', lambda *args: (opened.append(args), device)[1])
    camera = replace(config.cameras[0], kind='avfoundation', source='2', width=1280, height=720, capture_fps=30)
    worker = capture.CaptureWorker(camera, config)
    assert worker.watched is None
    worker.watch_interval = .001  # Would lose a numeric source treated as a path.
    worker.start()
    try:
        wait_until(lambda: worker.latest.sequence >= 3 and worker.capture_fps > 0)
        assert opened == [(2, cv2.CAP_AVFOUNDATION)]
        assert device.settings == [(cv2.CAP_PROP_FRAME_WIDTH, 1280), (cv2.CAP_PROP_FRAME_HEIGHT, 720), (cv2.CAP_PROP_FPS, 30)]
        assert worker.latest.get().image.shape == (480, 640, 3)
        assert (worker.status()['capture_width'], worker.status()['capture_height']) == (640, 480)
        assert worker.status()['connected']
    finally:
        worker.stop()
    assert device.released


@pytest.mark.parametrize('source', ['/dev/v4l/by-id/board-camera', '/dev/v4l/by-path/board-camera'])
@pytest.mark.parametrize('fmt,fps', [('YUYV', 5), ('', 0)])
def test_linux_v4l2_open_sequence_and_unplug_watch_are_unchanged(config, monkeypatch, source, fmt, fps):
    platform(monkeypatch, 'linux')
    opened, device = [], Camera()
    monkeypatch.setattr(cv2, 'VideoCapture', lambda *args: (opened.append(args), device)[1])
    camera = replace(config.cameras[0], kind='usb', source=source, width=320, height=240, capture_format=fmt, capture_fps=fps)
    cfg = replace(config, cameras=[camera, *config.cameras[1:]])
    worker = capture.CaptureWorker(camera, cfg)
    assert worker.watched == Path(source)
    assert worker._open() is device
    expected = [(cv2.CAP_PROP_BUFFERSIZE, 1)]
    if fmt:
        expected.append((cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'YUYV')))
    expected.extend([(cv2.CAP_PROP_FRAME_WIDTH, 320), (cv2.CAP_PROP_FRAME_HEIGHT, 240)])
    if fps:
        expected.append((cv2.CAP_PROP_FPS, 5))
    assert opened == [(source, cv2.CAP_V4L2)]
    assert device.settings == expected
    with pytest.raises(ValueError, match='never an index'):
        replace(config, cameras=[replace(camera, source='0'), *config.cameras[1:]])


def test_file_capture_keeps_default_backend_and_path_watch(config, monkeypatch):
    platform(monkeypatch, 'darwin')
    opened, device = [], Camera()
    monkeypatch.setattr(cv2, 'VideoCapture', lambda *args: (opened.append(args), device)[1])
    worker = capture.CaptureWorker(config.cameras[0], config)
    assert worker._open() is device
    assert opened == [(config.cameras[0].source,)] and device.settings == []
    assert worker.watched == Path(config.cameras[0].source)


def test_live_mac_example_has_one_live_source_and_no_board_simulation(monkeypatch):
    platform(monkeypatch, 'darwin')
    config = load_config(ROOT / 'demo-mac-camera.toml')
    active = [c for c in config.cameras if c.active]
    assert [(c.name, c.kind, c.source) for c in active] == [('left', 'avfoundation', '0')]
    assert (active[0].width, active[0].height, active[0].capture_fps) == (1280, 720, 30)
    assert config.detector_view == 'center_crop' and config.profile == 'demo'
    assert config.confidence == .35 and config.analysis_hz == 1
    assert config.mcu.mode == 'off' and config.lora.transport == 'simulated'
    assert config.data_dir != load_config(ROOT / 'demo-laptop.toml').data_dir


def test_native_mac_rejects_linux_fourcc_request(config, monkeypatch):
    platform(monkeypatch, 'darwin')
    cameras = [replace(c, kind='avfoundation', source='0', capture_format='YUYV') if c.name == 'left' else c for c in config.cameras]
    with pytest.raises(ValueError, match='AVFoundation.*capture_format'):
        replace(config, cameras=cameras)


def test_native_worker_cannot_open_avfoundation_on_linux(config, monkeypatch):
    platform(monkeypatch, 'linux')
    def forbidden(*args):
        raise AssertionError('Unsupported backend reached camera open')
    monkeypatch.setattr(cv2, 'VideoCapture', forbidden)
    worker = capture.CaptureWorker(replace(config.cameras[0], kind='avfoundation', source='0'), config)
    with pytest.raises(OSError, match='AVFoundation.*macOS'):
        worker._open()
