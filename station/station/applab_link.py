"""App Lab's shared Bridge API adapted to the station's McuLink interface."""
import logging
import threading
import time

from .mcu_protocol import READING_METHOD, STATE_METHOD

log = logging.getLogger(__name__)


class AppLabLink:
    kind = "applab"
    simulated = False

    def __init__(self, request_timeout=2.0, bridge=None, clock=time.time):
        self.bridge = bridge
        self.request_timeout = request_timeout
        self.clock = clock
        self.lock = threading.Lock()
        self.on_reading = None
        self.registered = False
        self.stopped = False
        self.last_ack_at = self.mcu_protocol = self.last_error = None
        self.unanswered = 0

    def start(self, on_reading):
        if self.bridge is None:
            from arduino.app_utils import Bridge
            self.bridge = Bridge
        self.on_reading = on_reading
        # Registration is retried by send_state, outside the telemetry handler.
        self._provide()

    def _error(self, exc):
        with self.lock:
            self.last_error = f"{type(exc).__name__}: {exc}"
        log.warning("App Lab MCU bridge: %s", self.last_error)

    def _provide(self):
        if self.registered or self.stopped:
            return
        try:
            self.bridge.provide(READING_METHOD, self._reading)
            with self.lock:
                self.registered = True
        except Exception as exc:
            self._error(exc)

    def _reading(self, *params):
        if self.stopped:
            return
        try:
            self.on_reading(list(params))
        except Exception as exc:
            self._error(exc)

    def send_state(self, state, seq):
        if self.stopped:
            return
        self._provide()
        if not self.registered:
            return
        try:
            result = self.bridge.call(STATE_METHOD, int(state), int(seq), timeout=self.request_timeout)
            with self.lock:
                self.last_ack_at = self.clock()
                self.mcu_protocol = result
                self.unanswered = 0
                self.last_error = None
        except Exception as exc:
            with self.lock:
                self.unanswered += 1
            self._error(exc)

    def stop(self):
        self.stopped = True
        if self.registered:
            try:
                self.bridge.unprovide(READING_METHOD)
            except Exception as exc:
                self._error(exc)
        with self.lock:
            self.registered = False

    def status(self):
        with self.lock:
            return {"transport": self.kind, "registered": self.registered,
                    "mcu_acknowledged_at": self.last_ack_at, "mcu_protocol": self.mcu_protocol,
                    "unanswered_requests": self.unanswered, "last_error": self.last_error}
