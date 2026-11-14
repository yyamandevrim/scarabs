"""Microcontroller bridge: protocol, firmware logic parity, flame events, LED state."""
import shutil
import socket
import sqlite3
import subprocess
import threading
import time
from auth_client import TestClient
import pytest
from station import msgpack_lite
from station.alarm import Detection
from station.mcu_bridge import McuBridge, requested_led
from station.mcu_link import RouterLink, SimulatedLink
from station.mcu_model import FlameDetector, LinkWatch, Settings, select_led
from station.mcu_protocol import (LED_DEGRADED, LED_FLAME, LED_LINUX_SILENT, LED_NORMAL, LED_SMOKE_PENDING,
                                  PROTOCOL_VERSION, McuConfig, parse_reading)
from station.runtime import Station
from station.storage import EventStore
from station.web import create_app
from conftest import ROOT, wait_until
from test_capture import EmptyDetector

FIRMWARE = ROOT.parent / "firmware"
VECTORS = FIRMWARE / "test" / "vectors.txt"


def reading(seq=1, triggered=False, level=10, led=LED_NORMAL, digital=None, linux_ok=True, raw=3900):
    return [PROTOCOL_VERSION, seq, seq * 500, raw, raw, level, 12, triggered if digital is None else digital, triggered, led, linux_ok]


# -- MessagePack -------------------------------------------------------------

@pytest.mark.parametrize("value,encoded", [
    (None, b"\xc0"), (True, b"\xc3"), (False, b"\xc2"), (5, b"\x05"), (-1, b"\xff"), (200, b"\xcc\xc8"),
    (70000, b"\xce\x00\x01\x11\x70"), (-200, b"\xd1\xff\x38"), ("acorn", b"\xa5acorn"),
    ([0, 1, "$/register", ["acorn_reading"]], b"\x94\x00\x01\xaa$/register\x91\xadacorn_reading"),
    ({"a": 1}, b"\x81\xa1a\x01"), (1.5, b"\xcb\x3f\xf8\x00\x00\x00\x00\x00\x00"),
])
def test_msgpack_known_encodings(value, encoded):
    assert msgpack_lite.pack(value) == encoded
    assert msgpack_lite.unpack(encoded) == value


def test_msgpack_stream_and_wide_types():
    value = [2, "acorn_reading", reading()] + ["x" * 40, list(range(20)), b"\x00\x01", 2**40, -2**40]
    data = msgpack_lite.pack(value) * 2
    unpacker = msgpack_lite.Unpacker()
    got = []
    for i in range(0, len(data), 7):  # arbitrary socket chunking
        unpacker.feed(data[i:i + 7])
        got.extend(unpacker)
    assert got == [value, value]
    assert msgpack_lite.unpack(b"\xca\x3f\xc0\x00\x00") == 1.5  # float32 from the MCU
    with pytest.raises(ValueError):
        msgpack_lite.unpack(b"\xc1")


# -- Firmware logic (Python port and the real C++) ---------------------------

def run_vectors(path):
    scenarios, steps = 0, 0
    s = Settings()
    det = watch = None
    for line in path.read_text().splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        if line.startswith("scenario "):
            name, det, watch = line.split()[1], FlameDetector(s), LinkWatch(s.linux_timeout_ms)
            scenarios += 1
            continue
        t, raw, dig, state, _, trig, led, level = line.split()
        t = int(t)
        det.sample(t, int(raw), dig == "1")
        if state != "-":
            watch.heard(t, int(state))
        got = select_led(det.flame_shown(t), watch.silent(t), watch.requested)
        assert int(det.triggered) == int(trig), f"{name} t={t}"
        assert got == int(led), f"{name} t={t}"
        if level != "-":
            assert det.level_permille() == int(level), f"{name} t={t}"
        steps += 1
    return scenarios, steps


def test_python_model_matches_shared_firmware_vectors():
    scenarios, steps = run_vectors(VECTORS)
    assert scenarios >= 10 and steps >= 50


def test_firmware_logic_compiles_and_passes_on_host(tmp_path):
    compiler = shutil.which("c++") or shutil.which("g++") or shutil.which("clang++")
    if not compiler:
        pytest.skip("No host C++ compiler")
    binary = tmp_path / "test_logic"
    subprocess.run([compiler, "-std=c++17", "-Wall", "-Wextra", "-Werror", f"-I{FIRMWARE/'acorn_mcu'}",
                    str(FIRMWARE / "test" / "test_logic.cpp"), "-o", str(binary)], check=True)
    out = subprocess.run([str(binary), str(VECTORS)], capture_output=True, text=True)
    assert out.returncode == 0, out.stdout
    assert " 0 failures" in out.stdout


def test_single_noisy_sample_and_smoothing():
    det = FlameDetector(Settings())
    for t in range(0, 1000, 10):
        det.sample(t, 4095 if t != 500 else 0, t == 500)  # one wild sample
    assert not det.triggered and det.level_permille() < 20
    analog = FlameDetector(Settings(analog_trigger_permille=600, analog_release_permille=400))
    analog.sample(0, 4095, False)
    analog.sample(10, 0, False)  # one dark->bright sample is smoothed below threshold
    assert analog.level_permille() < 600 and not analog.triggered


@pytest.mark.parametrize("flame,pending,cameras,expected", [
    (False, False, [{"active": True, "connected": True}], LED_NORMAL),
    (False, True, [{"active": True, "connected": True}], LED_SMOKE_PENDING),
    (False, False, [{"active": True, "connected": False}], LED_DEGRADED),
    (False, False, [{"active": True, "connected": True, "pipeline_error": "x"}], LED_DEGRADED),
    (False, False, [{"active": False, "connected": False}, {"active": True, "connected": True}], LED_NORMAL),
    (False, True, [{"active": True, "connected": False}], LED_SMOKE_PENDING),
    (True, True, [{"active": True, "connected": False}], LED_FLAME),
    (True, False, [], LED_FLAME),
])
def test_station_led_priority(flame, pending, cameras, expected):
    assert requested_led(flame, pending, cameras) == expected


@pytest.mark.parametrize("flame,silent,requested,expected", [
    (True, True, LED_NORMAL, LED_FLAME), (True, False, LED_SMOKE_PENDING, LED_FLAME),
    (False, True, LED_SMOKE_PENDING, LED_LINUX_SILENT), (False, True, LED_FLAME, LED_LINUX_SILENT),
    (False, False, LED_DEGRADED, LED_DEGRADED), (False, False, 99, LED_DEGRADED),
])
def test_mcu_led_priority(flame, silent, requested, expected):
    assert select_led(flame, silent, requested) == expected


def test_silent_linux_timeout_and_wraparound():
    watch = LinkWatch(5000)
    assert watch.silent(0)
    start = 0xFFFFFFFF - 1000
    watch.heard(start, LED_SMOKE_PENDING)
    assert not watch.silent((start + 4999) & 0xFFFFFFFF)
    assert watch.silent((start + 5000) & 0xFFFFFFFF)


def test_reading_validation():
    assert parse_reading(reading(triggered=True))["triggered"] is True
    for bad in ([], reading()[:5], [99] + reading()[1:], reading(level=2000), reading()[:7] + [1] + reading()[8:]):
        with pytest.raises(ValueError):
            parse_reading(bad)


# -- Router protocol, against a fake arduino-router -------------------------

class FakeRouter:
    """Speaks MessagePack-RPC like arduino-router; plays the MCU side."""

    def __init__(self, path, register_error=None, state_error=None):
        self.server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.server.bind(path)
        self.server.listen(1)
        self.received, self.responses, self.conn = [], [], None
        self.register_error, self.state_error = register_error, state_error
        self.thread = threading.Thread(target=self._serve, daemon=True)
        self.thread.start()

    def _serve(self):
        while True:
            try:
                conn, _ = self.server.accept()
            except OSError:
                return
            self.conn = conn
            unpacker = msgpack_lite.Unpacker()
            while True:
                try:
                    data = conn.recv(4096)
                except OSError:
                    break
                if not data:
                    break
                unpacker.feed(data)
                for msg in unpacker:
                    self.received.append(msg)
                    if msg[0] == 1:
                        self.responses.append(msg)
                    if msg[0] == 0 and msg[2] == "$/register":
                        self.send([1, msg[1], self.register_error, None if self.register_error else True])
                    elif msg[0] == 0 and msg[2] == "acorn_state":
                        self.send([1, msg[1], self.state_error, None if self.state_error else PROTOCOL_VERSION])

    def send(self, msg):
        self.conn.sendall(msgpack_lite.pack(msg))

    def drop(self):
        self.conn.shutdown(socket.SHUT_RDWR)
        self.conn.close()

    def close(self):
        self.server.close()


@pytest.fixture
def short_socket_dir(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)  # AF_UNIX paths are length-limited; use a relative one.
    return "r.sock"


def test_router_link_both_directions(short_socket_dir):
    router = FakeRouter(short_socket_dir)
    got = []
    link = RouterLink(short_socket_dir, request_timeout=.5, reconnect_seconds=.05)
    link.start(got.append)
    try:
        wait_until(lambda: link.status()["registered"])
        assert [0, router.received[0][1], "$/register", ["acorn_reading"]] == router.received[0]
        # Up: MCU notification and an MCU request both reach the station.
        router.send([2, "acorn_reading", reading(seq=7)])
        router.send([0, 55, "acorn_reading", reading(seq=8)])
        router.send([2, "something_else", [1]])
        wait_until(lambda: len(got) == 2)
        assert [r[1] for r in got] == [7, 8]
        wait_until(lambda: router.responses == [[1, 55, None, True]])
        # Down: state request carries (state, seq); MCU acknowledgement is recorded.
        link.send_state(LED_SMOKE_PENDING, 3)
        wait_until(lambda: link.status()["mcu_acknowledged_at"] is not None)
        assert router.received[-1][2:] == ["acorn_state", [LED_SMOKE_PENDING, 3]]
        assert link.status()["mcu_protocol"] == PROTOCOL_VERSION
        # Reconnect after the router drops the connection.
        router.drop()
        wait_until(lambda: sum(m[2] == "$/register" for m in router.received if m[0] == 0) == 2)
        wait_until(lambda: link.status()["registered"])
    finally:
        link.stop()
        router.close()


def test_router_link_reports_missing_sketch_and_unanswered(short_socket_dir):
    router = FakeRouter(short_socket_dir, state_error=[4, "method acorn_state not available"])
    link = RouterLink(short_socket_dir, request_timeout=.2, reconnect_seconds=.05)
    link.start(lambda r: None)
    try:
        wait_until(lambda: link.status()["registered"])
        link.send_state(LED_NORMAL, 1)
        wait_until(lambda: "not available" in (link.status()["last_error"] or ""))
        router.state_error = None
        link.send_state(LED_NORMAL, 2)
        wait_until(lambda: link.status()["last_error"] is None)
    finally:
        link.stop()
        router.close()


def test_router_link_without_router_keeps_retrying(short_socket_dir):
    link = RouterLink(short_socket_dir, reconnect_seconds=.05)
    link.start(lambda r: None)
    try:
        wait_until(lambda: "unavailable" in (link.status()["last_error"] or ""))
        link.send_state(LED_NORMAL, 1)  # dropped, never raises
        assert not link.status()["router_connected"]
    finally:
        link.stop()


def test_router_registration_conflict_retries(short_socket_dir):
    router = FakeRouter(short_socket_dir, register_error=[5, "route already exists: acorn_reading"])
    link = RouterLink(short_socket_dir, reconnect_seconds=.05)
    link.start(lambda r: None)
    try:
        wait_until(lambda: sum(m[2] == "$/register" for m in router.received if m[0] == 0) >= 2)
        assert not link.status()["registered"]
        assert "already exists" in link.status()["last_error"]
    finally:
        link.stop()
        router.close()


# -- Station side: flame events and LED state --------------------------------

class FakeLink:
    kind, simulated = "fake", False

    def __init__(self):
        self.sent = []

    def start(self, on_reading):
        self.on_reading = on_reading

    def send_state(self, state, seq):
        self.sent.append((state, seq))

    def stop(self):
        pass

    def status(self):
        return {"transport": "fake"}


class FakeStation:
    def __init__(self, store, cameras):
        self.store, self.cameras = store, cameras

    def status(self):
        return {"cameras": self.cameras}


def test_flame_trigger_becomes_its_own_event(tmp_path):
    store = EventStore(tmp_path)
    clock = [1000.0]
    station = FakeStation(store, [{"active": True, "connected": True}])
    bridge = McuBridge(station, McuConfig(mode="router"), link=FakeLink(), clock=lambda: clock[0])
    try:
        bridge.on_reading(reading(seq=1))
        assert store.events(kind="flame_sensor") == []
        bridge.tick()
        assert bridge.link.sent[-1][0] == LED_NORMAL
        bridge.on_reading(reading(seq=2, triggered=True, level=700, led=LED_FLAME))
        clock[0] += 1
        bridge.on_reading(reading(seq=3, triggered=True, level=850, led=LED_FLAME))
        bridge.tick()
        assert bridge.link.sent[-1][0] == LED_FLAME
        event = store.events(kind="flame_sensor")[0]
        assert event["kind"] == "flame_sensor" and event["title"] == "Flame-sensor trigger"
        assert event["camera"] is None and event["box"] is None and event["confidence"] is None
        assert event["opened_at"] == 1000 and event["closed_at"] is None and event["decision"] == "pending"
        assert event["details"]["trigger_reading"]["level_permille"] == 700
        assert event["details"]["peak_level_permille"] == 850 and event["details"]["source"] == "hardware"
        status = bridge.status()
        assert status["flame_sensor"]["triggered"] and status["flame_sensor"]["status_text"] == "Flame-sensor trigger"
        assert status["flame_sensor"]["open_event_id"] == event["id"]
        assert status["led"]["shown"]["name"] == "flame_sensor"
        assert store.events() == []  # camera list stays smoke-only by default
        clock[0] += 2
        bridge.on_reading(reading(seq=4, triggered=False, level=20))
        event = store.events(kind="flame_sensor")[0]
        assert event["closed_at"] == 1003 and event["details"]["closed_reason"] == "sensor_cleared"
        # A second trigger is a new event; losing the sensor closes it.
        bridge.on_reading(reading(seq=5, triggered=True, level=600))
        clock[0] += 10
        bridge.tick()
        events = store.events(kind="flame_sensor")
        assert len(events) == 2 and events[0]["details"]["closed_reason"] == "sensor_disconnected"
        assert not bridge.status()["flame_sensor"]["connected"]
        assert bridge.status()["flame_sensor"]["status_text"] == "Flame sensor disconnected"
        assert bridge.link.sent[-1][0] == LED_NORMAL  # stale flame reading no longer requests flame
        with pytest.raises(ValueError):
            bridge.on_reading([1, 2])
        assert bridge.status()["link"]["rejected_readings"] == 1
    finally:
        store.shutdown()


def test_led_request_follows_station_state(tmp_path):
    store = EventStore(tmp_path)
    cameras = [{"active": True, "connected": True}, {"active": True, "connected": True}]
    bridge = McuBridge(FakeStation(store, cameras), McuConfig(mode="router"), link=FakeLink())
    try:
        bridge.tick()
        assert bridge.link.sent[-1][0] == LED_NORMAL
        cameras[1]["connected"] = False
        bridge.tick()
        assert bridge.link.sent[-1][0] == LED_DEGRADED
        smoke = store.create("left", Detection((.1, .1, .2, .2), .5), time.time())
        bridge.tick()
        assert bridge.link.sent[-1][0] == LED_SMOKE_PENDING
        store.decide(smoke, "rejected", time.time())
        bridge.tick()
        assert bridge.link.sent[-1][0] == LED_DEGRADED
        flame = store.create_flame(time.time(), {})
        bridge.tick()
        assert bridge.link.sent[-1][0] == LED_DEGRADED  # pending flame-sensor rows are not smoke
        assert [s for _, s in bridge.link.sent] == [1, 2, 3, 4, 5]
        assert bridge.status()["led"]["requested"]["name"] == "degraded"
        assert flame
    finally:
        store.shutdown()


def test_off_mode_status():
    bridge = McuBridge(FakeStation(None, []), McuConfig())
    bridge.start()
    bridge.stop()
    status = bridge.status()
    assert status["mode"] == "off" and not status["flame_sensor"]["configured"]
    assert status["flame_sensor"]["status_text"] == "Flame sensor not configured"


def test_mcu_config_validation():
    with pytest.raises(ValueError):
        McuConfig(mode="serial")
    with pytest.raises(ValueError):
        McuConfig(state_interval=0)


# -- Whole station with the simulated MCU, through the HTTP API ---------------

def test_simulated_flame_through_api(config):
    station = Station(config, detector=EmptyDetector())
    station.mcu = McuBridge(station, McuConfig(mode="simulated", state_interval=.05, reading_timeout=1),
                            link=SimulatedLink(Settings(linux_timeout_ms=400), reading_interval_ms=50))
    with TestClient(create_app(station)) as client:
        wait_until(lambda: client.get("/api/mcu").json()["flame_sensor"]["connected"])
        status = client.get("/api/mcu").json()
        assert status["simulated"] and status["flame_sensor"]["simulated"]
        assert status["flame_sensor"]["scope"] == "station_local_short_range"
        assert not status["flame_sensor"]["triggered"]
        assert client.get("/api/status").json()["mcu"]["mode"] == "simulated"
        # Missing files: both cameras disconnected, so the station asks for "degraded".
        wait_until(lambda: client.get("/api/mcu").json()["led"]["shown"]["name"] == "degraded")
        assert client.post("/api/mcu/simulate", json={"flame": True}).status_code == 200
        wait_until(lambda: client.get("/api/events", params={"kind": "flame_sensor"}).json())
        event = client.get("/api/events", params={"kind": "flame_sensor"}).json()[0]
        assert event["title"] == "Flame-sensor trigger" and event["details"]["source"] == "simulated"
        assert client.get("/api/mcu").json()["led"]["shown"]["name"] == "flame_sensor"
        assert client.get("/api/events").json() == []
        assert [e["kind"] for e in client.get("/api/events", params={"kind": "all"}).json()] == ["flame_sensor"]
        assert client.post(f"/api/events/{event['id']}/decision", json={"decision": "rejected"}).status_code == 200
        client.post("/api/mcu/simulate", json={"flame": False})
        wait_until(lambda: client.get("/api/events", params={"kind": "flame_sensor"}).json()[0]["closed_at"], timeout=4)
        # Linux silent: the simulated sketch stops hearing the station and says so itself.
        client.post("/api/mcu/simulate", json={"linux_silent": True})
        wait_until(lambda: client.get("/api/mcu").json()["led"]["shown"]["name"] == "linux_silent", timeout=6)
        assert client.get("/api/mcu").json()["led"]["mcu_hears_station"] is False
        client.post("/api/mcu/simulate", json={"linux_silent": False})
        wait_until(lambda: client.get("/api/mcu").json()["led"]["shown"]["name"] == "degraded")
        assert client.get("/api/events", params={"kind": "bogus"}).status_code == 422


def test_simulate_refused_without_simulated_mcu(config):
    station = Station(config, detector=EmptyDetector())
    try:
        with TestClient(create_app(station, manage_lifecycle=False)) as client:
            assert client.post("/api/mcu/simulate", json={"flame": True}).status_code == 409
            assert client.get("/api/mcu").json()["mode"] == "off"
    finally:
        station.stop()
        station.store.shutdown()


# -- Schema migration ----------------------------------------------------------

def test_old_database_is_migrated_in_place(tmp_path):
    db = sqlite3.connect(tmp_path / "events.sqlite3")
    db.execute("""CREATE TABLE events (
        id TEXT PRIMARY KEY, camera TEXT NOT NULL, opened_at REAL NOT NULL,
        last_seen REAL NOT NULL, closed_at REAL, box TEXT NOT NULL,
        confidence REAL NOT NULL, snapshot TEXT, clip TEXT,
        decision TEXT NOT NULL DEFAULT 'pending' CHECK(decision IN ('pending','confirmed','rejected')),
        decided_at REAL, media_error TEXT)""")
    db.execute("INSERT INTO events(id,camera,opened_at,last_seen,box,confidence,decision,decided_at,clip) VALUES('a'||hex(randomblob(15)),'left',10,20,'[0.1,0.2,0.3,0.4]',0.45,'confirmed',21,'old.avi')")
    db.commit()
    db.close()
    for _ in range(2):  # opening twice must be harmless
        store = EventStore(tmp_path)
        try:
            old = store.events()[0]
            assert old["kind"] == "smoke" and old["title"] == "Smoke suspicion"
            assert old["decision"] == "confirmed" and old["clip"] == "old.avi" and old["box"] == [.1, .2, .3, .4]
            assert old["confidence"] == old["latest_confidence"] == .45
            assert old["alarm_confidence"] is None and old["peak_confidence"] is None  # never recorded
            assert store.pending_count() == 0
        finally:
            store.shutdown()
    store = EventStore(tmp_path)
    try:
        store.create_flame(30, {"x": 1})
        assert store.pending_count("flame_sensor") == 1 and len(store.events(kind="all")) == 2
    finally:
        store.shutdown()
