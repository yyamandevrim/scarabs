"""Station side of the microcontroller: flame-sensor readings up, station state down.

The KY-026 is a local, short-range infrared flame sensor at the station. Its
triggers are stored as their own event kind ("flame_sensor") and are never
merged with camera "suspected smoke" events.
"""
from __future__ import annotations
import logging
import threading
import time
from fastapi import HTTPException
from pydantic import BaseModel
from .mcu_link import RouterLink, SimulatedLink
from .mcu_protocol import (FLAME_SCOPE_NOTE, FLAME_TRIGGERED_TEXT, LED_DEGRADED, LED_FLAME, LED_NORMAL,
                           LED_SMOKE_PENDING, McuConfig, led_info, parse_reading)

log = logging.getLogger(__name__)


def make_link(cfg: McuConfig):
    if cfg.mode == "router":
        return RouterLink(cfg.socket, cfg.request_timeout, cfg.reconnect_seconds)
    if cfg.mode == "simulated":
        return SimulatedLink()
    return None


def requested_led(flame_triggered, pending_smoke, cameras):
    """Station-side choice, highest priority first. The MCU adds two of its own on
    top: its local flame trigger and 'Linux silent' (see acorn_logic.h select_led)."""
    if flame_triggered:
        return LED_FLAME
    if pending_smoke:
        return LED_SMOKE_PENDING
    if any(c.get("active") and (not c.get("connected") or c.get("pipeline_error")) for c in cameras):
        return LED_DEGRADED
    return LED_NORMAL


class McuBridge:
    def __init__(self, station, cfg: McuConfig | None = None, link=None, clock=time.time):
        self.station = station
        self.cfg = cfg or McuConfig()
        self.link = link if link is not None else make_link(self.cfg)
        self.clock = clock
        self.lock = threading.Lock()
        self.stop_event = threading.Event()
        self.thread = None
        self.reading = None
        self.reading_at = None
        self.rejected = 0
        self.flame_event = None   # {"id", "peak_level_permille", "trigger": reading}
        self.requested = None
        self.seq = 0

    @property
    def mode(self):
        return self.cfg.mode if self.link is not None else "off"

    def start(self):
        if self.link is None:
            return
        self.link.start(self.on_reading)
        self.thread = threading.Thread(target=self._run, name="mcu-state", daemon=True)
        self.thread.start()

    def stop(self):
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=5)
        if self.link is not None:
            self.link.stop()
        with self.lock:
            if self.flame_event:
                self._close_flame(self.clock(), "station_stopped")

    # -- readings (link thread) -------------------------------------------
    def on_reading(self, params):
        try:
            reading = parse_reading(params)
        except ValueError:
            with self.lock:
                self.rejected += 1
            raise
        now = self.clock()
        with self.lock:
            self.reading, self.reading_at = reading, now
            event = self.flame_event
            if reading["triggered"] and event is None:
                details = self._details(reading, reading)
                event_id = self.station.store.create_flame(now, details)
                self.flame_event = {"id": event_id, "trigger": reading, "peak": reading}
                log.info("Flame sensor triggered (local sensor): event %s, level %d/1000", event_id, reading["level_permille"])
            elif event is not None:
                if reading["level_permille"] > event["peak"]["level_permille"]:
                    event["peak"] = reading
                if reading["triggered"]:
                    self.station.store.update_flame(event["id"], now, self._details(event["trigger"], event["peak"]))
                else:
                    self._close_flame(now, "sensor_cleared", reading)

    def _details(self, trigger, peak, closed_reason=None, last=None):
        details = {"source": "simulated" if self.link.simulated else "hardware",
                   "sensor": "KY-026 local infrared flame sensor",
                   "trigger_reading": self._public(trigger),
                   "peak_level_permille": peak["level_permille"],
                   "peak_level": peak["level_permille"] / 1000}
        if closed_reason:
            details["closed_reason"] = closed_reason
        if last is not None:
            details["last_reading"] = self._public(last)
        return details

    @staticmethod
    def _public(r):
        return {k: r[k] for k in ("seq", "uptime_ms", "raw", "smoothed_raw", "level_permille", "adc_bits", "digital_active", "triggered")}

    def _close_flame(self, now, reason, last=None):
        event = self.flame_event
        self.flame_event = None
        store = self.station.store
        store.update_flame(event["id"], now, self._details(event["trigger"], event["peak"], reason, last))
        store.close_event(event["id"], now)

    # -- state (own thread) ------------------------------------------------
    def connected(self, now=None):
        now = self.clock() if now is None else now
        return self.reading_at is not None and now - self.reading_at <= self.cfg.reading_timeout

    def compute_requested(self):
        cameras = self.station.status()["cameras"]
        with self.lock:
            flame = bool(self.reading and self.reading["triggered"] and self.connected())
        return requested_led(flame, self.station.store.pending_count("smoke") > 0, cameras)

    def tick(self):
        now = self.clock()
        with self.lock:
            if self.flame_event and not self.connected(now):
                self._close_flame(now, "sensor_disconnected")
        try:
            state = self.compute_requested()
        except Exception:
            log.exception("Could not compute LED state")
            state = LED_DEGRADED
        self.seq += 1
        with self.lock:
            self.requested = state
        self.link.send_state(state, self.seq)

    def _run(self):
        while not self.stop_event.is_set():
            self.tick()
            self.stop_event.wait(self.cfg.state_interval)

    # -- API ----------------------------------------------------------------
    def status(self):
        now = self.clock()
        with self.lock:
            r, at, requested, event = self.reading, self.reading_at, self.requested, self.flame_event
            connected = self.connected(now)
            rejected = self.rejected
        simulated = bool(self.link is not None and self.link.simulated)
        if self.link is None:
            text = "Alev sensörü yapılandırılmamış"
        elif not connected:
            text = "Alev sensörü bağlı değil"
        elif r["triggered"]:
            text = FLAME_TRIGGERED_TEXT
        else:
            text = "Alev sensörü normal"
        live = r if connected else None
        sensor = {
            "kind": "local_flame_sensor", "model": "Joy-IT KY-026", "scope": "station_local_short_range",
            "note": FLAME_SCOPE_NOTE, "simulated": simulated, "configured": self.link is not None,
            "connected": connected, "status_text": text, "last_update": at,
            "level": live["level_permille"] / 1000 if live else None,
            "level_permille": live["level_permille"] if live else None,
            "level_note": "relative infrared intensity 0..1, uncalibrated; not a distance or fire size",
            "raw": live["raw"] if live else None, "smoothed_raw": live["smoothed_raw"] if live else None,
            "adc_bits": live["adc_bits"] if live else None,
            "digital_active": live["digital_active"] if live else None,
            "triggered": bool(live and live["triggered"]),
            "open_event_id": event["id"] if event else None,
        }
        led = {"requested": led_info(requested),
               "shown": led_info(r["led"]) if connected else None,
               "mcu_hears_station": r["linux_ok"] if connected else None,
               "simulated": simulated}
        link = self.link.status() if self.link is not None else {"transport": "off"}
        link.update(rejected_readings=rejected, mcu_uptime_ms=live["uptime_ms"] if live else None)
        return {"mode": self.mode, "simulated": simulated, "link": link, "flame_sensor": sensor, "led": led}


class Simulation(BaseModel):
    flame: bool | None = None
    linux_silent: bool | None = None


def register_routes(app, station):
    @app.get("/api/mcu")
    def mcu_status():
        return station.mcu.status()

    @app.post("/api/mcu/simulate")
    def mcu_simulate(body: Simulation):
        link = station.mcu.link
        if not isinstance(link, SimulatedLink):
            raise HTTPException(409, "Simülasyon yalnızca mcu.mode = \"simulated\" iken kullanılabilir")
        link.simulate(flame=body.flame, linux_silent=body.linux_silent)
        return {"ok": True, "simulated": True, "flame": body.flame, "linux_silent": body.linux_silent}
