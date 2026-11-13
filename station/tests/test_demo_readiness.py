"""Fixes from the jury dress rehearsal: live dropout, overlay text, confidence
fields, machine identity and the pre-demo event reset."""
from dataclasses import replace
from pathlib import Path
import shutil
import subprocess
import sys
import time
import cv2
import numpy as np
from auth_client import TestClient
import pytest
from station import datalock, machine, maintenance, overlay_text
from station.alarm import Detection
from station.capture import CaptureWorker
from station.detector import annotate
from station.runtime import Station
from station.storage import EventStore
from station.web import create_app
from conftest import ROOT, wait_until
from test_capture import EmptyDetector


def write_clip(path, frames=100):
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"MJPG"), 25, (160, 90))
    for i in range(frames):
        writer.write(np.full((90, 160, 3), i % 255, np.uint8))
    writer.release()


# -- Live dropout of a file source ---------------------------------------------

def test_removed_file_source_is_lost_live_and_recovers(config, video, tmp_path):
    left = tmp_path / "left.avi"
    shutil.copy(video, left)
    cameras = [replace(c, source=str(left if c.name == "left" else video), width=160, height=90) for c in config.cameras]
    station = Station(replace(config, cameras=cameras, retry_seconds=.1), detector=EmptyDetector())
    with TestClient(create_app(station)) as client:
        def slot(name):
            return {c["name"]: c for c in client.get("/api/status").json()["cameras"]}[name]
        wait_until(lambda: slot("left")["connected"] and slot("centre")["connected"])
        parked = left.with_name(left.name + ".unplugged")
        left.rename(parked)  # what `forest-station unplug left` does
        wait_until(lambda: slot("left")["status_text"] == "bağlantı koptu", timeout=2)
        before = station.metrics["centre"]["analyses"]
        wait_until(lambda: station.metrics["centre"]["analyses"] >= before + 2)
        assert slot("centre")["connected"]
        assert slot("right")["status_text"] == "takılı, bağlı değil"
        assert client.get("/api/cameras/left/frame.jpg").status_code == 503
        parked.rename(left)
        wait_until(lambda: slot("left")["connected"], timeout=3)


def test_looping_file_is_reopened_not_rewound(config, tmp_path):
    clip = tmp_path / "short.avi"
    write_clip(clip, frames=3)
    worker = CaptureWorker(replace(config.cameras[0], source=str(clip), width=160, height=90), replace(config, retry_seconds=5))
    worker.watch_interval = 1e9  # isolate the loop-point check
    opened = []
    real_open = worker._open
    worker.factory = lambda: (opened.append(1), real_open())[1]
    worker.start()
    try:
        wait_until(lambda: len(opened) >= 2)  # reopened at the loop point
        clip.unlink()
        wait_until(lambda: not worker.status()["connected"])
        assert "reopen" in worker.status()["error"]
    finally:
        worker.stop()


def test_unplug_and_replug_commands(config, tmp_path):
    clip = tmp_path / "centre.webm"
    clip.write_bytes(b"x")
    cfg = replace(config, cameras=[replace(c, source=str(clip)) if c.name == "centre" else c for c in config.cameras])
    assert "unplugged" in maintenance.unplug(cfg, "centre")
    assert not clip.exists() and clip.with_name("centre.webm.unplugged").exists()
    assert "already" in maintenance.unplug(cfg, "centre")
    assert "replugged" in maintenance.replug(cfg, "centre")
    assert clip.exists()
    with pytest.raises(ValueError, match="not active"):
        maintenance.unplug(cfg, "right")
    usb = replace(cfg, cameras=[replace(c, kind="usb", source="/dev/v4l/by-id/x") if c.name == "left" else c for c in cfg.cameras])
    with pytest.raises(ValueError, match="USB"):
        maintenance.unplug(usb, "left")


# -- Overlay text ----------------------------------------------------------------

def ink(text, scale=1.0, thickness=2):
    image = np.zeros((80, 400), np.uint8)
    overlay_text.put_text(image, text, (10, 50), scale, 255, thickness)
    ys, xs = np.nonzero(image)
    return image, ys.min(), ys.max()


def test_turkish_letters_get_their_marks():
    _, top_u, _ = ink("u")
    _, top_ue, _ = ink("ü")
    _, _, bottom_s = ink("s")
    _, _, bottom_sc = ink("ş")
    assert top_ue < top_u - 3, "ü needs dots above"
    assert bottom_sc > bottom_s + 3, "ş needs a cedilla below"
    for ch in "çğıİöşüÇĞÖŞÜ":
        assert ink(ch)[0].any()
    # Same advance width as the ASCII spelling, so layout is unchanged.
    assert overlay_text.text_size("Duman şüphesi %62", 1, 2)[0][0] == cv2.getTextSize("Duman suphesi %62", cv2.FONT_HERSHEY_SIMPLEX, 1, 2)[0][0]


def test_snapshot_label_is_not_question_marks():
    frame = np.full((360, 640, 3), 100, np.uint8)
    out = annotate(frame, [Detection((.1, .3, .5, .7), .62)])
    # OpenCV renders unsupported characters as "?"; our label must differ from that.
    wrong = frame.copy()
    cv2.putText(wrong, "Duman ??phesi %62", (0, 0), cv2.FONT_HERSHEY_SIMPLEX, .6, (0, 0, 0), 1)
    assert not np.array_equal(out, wrong) and out.shape == frame.shape
    import inspect
    from station import detector
    assert "Duman şüphesi" in inspect.getsource(detector.annotate)


# -- Confidence fields -------------------------------------------------------------

def test_alarm_peak_and_latest_confidence(tmp_path):
    store = EventStore(tmp_path)
    try:
        event_id = store.create("left", Detection((.1, .2, .3, .4), .62), 100)
        store.extend(event_id, Detection((.1, .2, .3, .4), .80), 101)
        store.extend(event_id, Detection((.1, .2, .3, .4), .45), 102)
        event = store.events()[0]
        assert event["alarm_confidence"] == .62  # what the snapshot and clip overlay show
        assert event["peak_confidence"] == .80
        assert event["latest_confidence"] == event["confidence"] == .45
    finally:
        store.shutdown()


# -- Machine identity ----------------------------------------------------------------

def test_machine_identity_in_status(config):
    station = Station(config, detector=EmptyDetector())
    try:
        with TestClient(create_app(station, manage_lifecycle=False)) as client:
            ident = client.get("/api/status").json()["measured_on"]
        assert set(ident) >= {"system", "architecture", "cpu_model", "board_model", "is_uno_q", "label"}
        assert ident["label"].startswith("Ölçüm bu cihazda")
        if sys.platform == "darwin":
            assert ident["is_uno_q"] is False and "UNO Q değil" in ident["label"]
    finally:
        station.stop()
        station.store.shutdown()


def test_uno_q_detection_from_device_tree():
    board = machine.describe("Linux", "aarch64", "6.16", "Cortex-A53", "Arduino UNO Q")
    assert board["is_uno_q"] and board["label"].endswith("Arduino UNO Q")
    mac = machine.describe("Darwin", "arm64", "27.0", "Apple M5", None)
    assert not mac["is_uno_q"] and "Apple M5" in mac["label"]


# -- Pre-demo reset ----------------------------------------------------------------------

def test_archive_and_delete_events(tmp_path):
    data = tmp_path / "data"
    store = EventStore(data)
    store.create("left", Detection((.1, .2, .3, .4), .6), time.time())
    (store.media / "deadbeef.jpg").write_bytes(b"jpg")
    store.shutdown()
    result = maintenance.archive_events(data)
    assert result["action"] == "archived" and result["events"] == 1 and result["media_files"] == 1
    archived = EventStore(Path(result["archive"]))
    try:
        assert len(archived.events()) == 1  # archive is a usable, self-contained store
    finally:
        archived.shutdown()
    fresh = EventStore(data)
    assert fresh.events() == []
    fresh.create("left", Detection((.1, .2, .3, .4), .6), time.time())
    fresh.shutdown()
    assert maintenance.archive_events(data, delete=True)["action"] == "deleted"
    assert not (data / "events.sqlite3").exists() and (data / "archive").is_dir()


def test_archive_refused_while_server_runs(config):
    station = Station(config, detector=EmptyDetector())
    with TestClient(create_app(station)):
        assert datalock.in_use(config.data_dir)
        with pytest.raises(datalock.DataDirBusy):
            maintenance.archive_events(config.data_dir)
        with pytest.raises(datalock.DataDirBusy):
            datalock.acquire(config.data_dir)  # a second server on the same data
    assert not datalock.in_use(config.data_dir)


def test_archive_cli_requires_typed_confirmation(tmp_path):
    cfg = tmp_path / "c.toml"
    cfg.write_text((ROOT / "config.toml").read_text().replace('data_dir = "data"', f'data_dir = "{tmp_path / "d"}"'))
    store = EventStore(tmp_path / "d")
    store.create("left", Detection((.1, .2, .3, .4), .6), time.time())
    store.shutdown()
    cmd = [sys.executable, "-m", "station.cli", "--config", str(cfg), "archive-events"]
    no = subprocess.run(cmd, input="yes\n", capture_output=True, text=True, cwd=ROOT)
    assert no.returncode == 1 and "nothing changed" in no.stderr
    assert (tmp_path / "d" / "events.sqlite3").exists()
    ok = subprocess.run(cmd, input="ARCHIVE\n", capture_output=True, text=True, cwd=ROOT)
    assert ok.returncode == 0, ok.stderr
    assert '"archived"' in ok.stdout and not (tmp_path / "d" / "events.sqlite3").exists()
