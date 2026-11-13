"""Hardware access to the UNO Q microcontroller, behind one small interface.

- RouterLink: the real board. Connects to arduino-router's Unix socket
  (MessagePack-RPC), registers ``acorn_reading`` to receive the sketch's
  notifications, and calls the sketch's ``acorn_state``.
- SimulatedLink: an in-process model of the sketch (same logic as the
  firmware, see mcu_model.py) for tests and demos without the board.
"""
from __future__ import annotations
import logging
import socket
import threading
import time
from typing import Callable, Protocol
from . import msgpack_lite
from .mcu_model import FlameDetector, LinkWatch, Settings, select_led
from .mcu_protocol import PROTOCOL_VERSION, READING_METHOD, STATE_METHOD

REQUEST, RESPONSE, NOTIFY = 0, 1, 2
log = logging.getLogger(__name__)


class McuLink(Protocol):
    kind: str
    simulated: bool

    def start(self, on_reading: Callable[[list], None]) -> None: ...
    def send_state(self, state: int, seq: int) -> None: ...
    def stop(self) -> None: ...
    def status(self) -> dict: ...


class RouterLink:
    kind = "router"
    simulated = False

    def __init__(self, socket_path, request_timeout=2.0, reconnect_seconds=2.0, clock=time.time):
        self.socket_path = str(socket_path)
        self.request_timeout = request_timeout
        self.reconnect_seconds = reconnect_seconds
        self.clock = clock
        self.on_reading = None
        self.sock = None
        self.write_lock = threading.Lock()
        self.lock = threading.Lock()
        self.stop_event = threading.Event()
        self.thread = None
        self.next_id = 1
        self.pending = {}          # msgid -> (method, sent_at)
        self.register_id = None
        self.router_connected = False
        self.registered = False
        self.last_error = None
        self.last_ack_at = None
        self.mcu_protocol = None
        self.unanswered = 0

    def start(self, on_reading):
        self.on_reading = on_reading
        self.thread = threading.Thread(target=self._run, name="mcu-router", daemon=True)
        self.thread.start()

    def stop(self):
        self.stop_event.set()
        self._close()
        if self.thread:
            self.thread.join(timeout=5)

    def status(self):
        with self.lock:
            return {"transport": "router", "socket": self.socket_path, "router_connected": self.router_connected,
                    "registered": self.registered, "mcu_acknowledged_at": self.last_ack_at,
                    "mcu_protocol": self.mcu_protocol, "unanswered_requests": self.unanswered,
                    "last_error": self.last_error}

    def send_state(self, state, seq):
        self._expire_pending()
        self._request(STATE_METHOD, [int(state), int(seq)])

    # -- internals -------------------------------------------------------
    def _request(self, method, params):
        with self.lock:
            msgid = self.next_id
            self.next_id = self.next_id % 0x7FFFFFFF + 1
            self.pending[msgid] = (method, self.clock())
        if not self._send([REQUEST, msgid, method, params]):
            with self.lock:
                self.pending.pop(msgid, None)
            return None
        return msgid

    def _send(self, message):
        data = msgpack_lite.pack(message)
        with self.write_lock:
            if self.sock is None:
                return False
            try:
                self.sock.sendall(data)
                return True
            except OSError as exc:
                self._set_error(f"send failed: {exc}")
                return False

    def _set_error(self, text):
        with self.lock:
            if text != self.last_error:
                log.warning("MCU bridge: %s", text)
            self.last_error = text

    def _expire_pending(self):
        now = self.clock()
        with self.lock:
            for msgid, (method, sent) in list(self.pending.items()):
                if now - sent > self.request_timeout:
                    del self.pending[msgid]
                    if method == STATE_METHOD:
                        self.unanswered += 1
                        self.last_error = "MCU did not answer acorn_state in time"

    def _close(self):
        with self.write_lock:
            if self.sock is not None:
                try:
                    self.sock.close()
                except OSError:
                    pass
                self.sock = None
        with self.lock:
            self.router_connected = self.registered = False
            self.pending.clear()

    def _run(self):
        while not self.stop_event.is_set():
            try:
                sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                sock.settimeout(0.2)
                sock.connect(self.socket_path)
            except OSError as exc:
                self._set_error(f"router socket unavailable: {exc}")
                self.stop_event.wait(self.reconnect_seconds)
                continue
            with self.write_lock:
                self.sock = sock
            with self.lock:
                self.router_connected = True
            self.register_id = self._request("$/register", [READING_METHOD])
            unpacker = msgpack_lite.Unpacker()
            try:
                while not self.stop_event.is_set():
                    try:
                        data = sock.recv(4096)
                    except socket.timeout:
                        continue
                    if not data:
                        raise OSError("router closed the connection")
                    unpacker.feed(data)
                    for message in unpacker:
                        self._handle(message)
            except (OSError, ValueError) as exc:
                if not self.stop_event.is_set():
                    self._set_error(f"router connection lost: {exc}")
            self._close()
            self.stop_event.wait(self.reconnect_seconds)

    def _handle(self, message):
        if not isinstance(message, list) or not message:
            raise ValueError("malformed MessagePack-RPC message")
        kind = message[0]
        if kind == RESPONSE and len(message) == 4:
            _, msgid, error, result = message
            with self.lock:
                method, _ = self.pending.pop(msgid, (None, None))
            if msgid == self.register_id:
                with self.lock:
                    self.registered = error is None
                if error is not None:
                    # e.g. another process already registered acorn_reading.
                    raise OSError(f"could not register {READING_METHOD}: {error}")
            elif method == STATE_METHOD:
                if error is None:
                    with self.lock:
                        self.last_ack_at, self.mcu_protocol, self.unanswered = self.clock(), result, 0
                        if self.last_error and "acorn_state" in self.last_error:
                            self.last_error = None
                else:
                    # "method acorn_state not available": sketch not running or not registered yet.
                    self._set_error(f"acorn_state failed: {error}")
        elif kind == NOTIFY and len(message) == 3:
            _, method, params = message
            if method == READING_METHOD:
                self._deliver(params)
        elif kind == REQUEST and len(message) == 4:
            _, msgid, method, params = message
            if method == READING_METHOD:
                self._deliver(params)
                self._send([RESPONSE, msgid, None, True])
            else:
                self._send([RESPONSE, msgid, f"method {method} not provided by station", None])

    def _deliver(self, params):
        try:
            self.on_reading(params)
        except Exception as exc:  # a bad reading must not drop the connection
            self._set_error(f"rejected reading: {exc}")


class SimulatedLink:
    """Runs the firmware logic in-process with simulated sensor inputs."""
    kind = "simulated"
    simulated = True
    DARK_RAW, FLAME_RAW = 3900, 700  # more infrared = lower voltage on the KY-026

    def __init__(self, settings: Settings | None = None, reading_interval_ms=500, tick=0.01):
        self.settings = settings or Settings()
        self.detector = FlameDetector(self.settings)
        self.watch = LinkWatch(self.settings.linux_timeout_ms)
        self.reading_interval_ms = reading_interval_ms
        self.tick = tick
        self.lock = threading.Lock()
        self.stop_event = threading.Event()
        self.thread = None
        self.on_reading = None
        self.raw, self.digital = self.DARK_RAW, False
        self.linux_silenced = False
        self.started_ms = None
        self.seq = 0
        self.led = 0

    def _now_ms(self):
        return int(time.monotonic() * 1000) & 0xFFFFFFFF

    def start(self, on_reading):
        self.on_reading = on_reading
        self.started_ms = self._now_ms()
        self.thread = threading.Thread(target=self._run, name="mcu-simulated", daemon=True)
        self.thread.start()

    def stop(self):
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=5)

    def status(self):
        with self.lock:
            return {"transport": "simulated", "linux_messages_ignored": self.linux_silenced}

    def send_state(self, state, seq):
        with self.lock:
            if not self.linux_silenced:
                self.watch.heard(self._now_ms(), int(state))

    def simulate(self, flame=None, linux_silent=None):
        with self.lock:
            if flame is not None:
                self.raw, self.digital = (self.FLAME_RAW, True) if flame else (self.DARK_RAW, False)
            if linux_silent is not None:
                self.linux_silenced = bool(linux_silent)

    def _run(self):
        last_sent, last_triggered = None, False
        while not self.stop_event.is_set():
            now = self._now_ms()
            with self.lock:
                self.detector.sample(now, self.raw, self.digital)
                silent = self.watch.silent(now)
                self.led = select_led(self.detector.flame_shown(now), silent, self.watch.requested)
                d = self.detector
                changed = d.triggered != last_triggered
                due = last_sent is None or ((now - last_sent) & 0xFFFFFFFF) >= self.reading_interval_ms
                params = None
                if changed or due:
                    self.seq += 1
                    params = [PROTOCOL_VERSION, self.seq, (now - self.started_ms) & 0xFFFFFFFF, d.last_raw,
                              d.smoothed_raw(), d.level_permille(), 12, d.digital, d.triggered, self.led, not silent]
                    last_sent, last_triggered = now, d.triggered
            if params is not None:
                # Same wire encoding as the real bridge.
                self.on_reading(msgpack_lite.unpack(msgpack_lite.pack(params)))
            self.stop_event.wait(self.tick)
