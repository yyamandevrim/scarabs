"""Python port of firmware/acorn_mcu/acorn_logic.h, used by the simulated MCU.

Kept line-for-line equivalent (including C integer truncation); both versions
are checked against firmware/test/vectors.txt.
"""
from dataclasses import dataclass
from .mcu_protocol import LED_DEGRADED, LED_FLAME, LED_LINUX_SILENT, LED_NORMAL, LED_SMOKE_PENDING

U32 = 0xFFFFFFFF


def _elapsed(now, since):
    return (now - since) & U32


def _cdiv(a, b):
    """C/C++ integer division (truncates toward zero)."""
    q = abs(a) // abs(b)
    return q if (a >= 0) == (b > 0) else -q


@dataclass
class Settings:
    adc_max: int = 4095
    analog_flame_lowers_voltage: bool = True
    ema_shift: int = 3
    trigger_ms: int = 150
    release_ms: int = 1000
    analog_trigger_permille: int = 0
    analog_release_permille: int = 0
    hold_ms: int = 3000
    linux_timeout_ms: int = 5000


class FlameDetector:
    def __init__(self, s: Settings):
        self.s = s
        self.primed = False
        self.ema16 = 0
        self.last_raw = 0
        self.digital = False
        self.analog_active = False
        self.triggered = False
        self.changing = False
        self.change_since = 0
        self.ever_released = False
        self.released_at = 0

    def sample(self, now, raw, digital_active):
        s = self.s
        raw = min(raw, s.adc_max)
        x16 = raw * 16
        if not self.primed:
            self.ema16, self.primed = x16, True
        else:
            self.ema16 += _cdiv(x16 - self.ema16, 1 << s.ema_shift)
        self.last_raw, self.digital = raw, bool(digital_active)
        level = self.level_permille()
        if s.analog_trigger_permille > 0:
            if not self.analog_active and level >= s.analog_trigger_permille:
                self.analog_active = True
            elif self.analog_active and level < s.analog_release_permille:
                self.analog_active = False
        value = self.digital or self.analog_active
        if value == self.triggered:
            self.changing = False
        else:
            if not self.changing:
                self.changing, self.change_since = True, now
            need = s.trigger_ms if value else s.release_ms
            if _elapsed(now, self.change_since) >= need:
                self.triggered, self.changing = value, False
                if not self.triggered:
                    self.released_at = now
                self.ever_released = self.ever_released or not self.triggered

    def smoothed_raw(self):
        return (self.ema16 + 8) // 16

    def level_permille(self):
        v = min(self.smoothed_raw(), self.s.adc_max)
        if self.s.analog_flame_lowers_voltage:
            v = self.s.adc_max - v
        return (v * 1000 + self.s.adc_max // 2) // self.s.adc_max

    def flame_shown(self, now):
        if self.triggered:
            return True
        return self.ever_released and _elapsed(now, self.released_at) < self.s.hold_ms


class LinkWatch:
    def __init__(self, timeout_ms):
        self.timeout = timeout_ms
        self.last = 0
        self.ever = False
        self.requested = LED_NORMAL

    def heard(self, now, requested):
        self.last, self.ever, self.requested = now, True, requested

    def silent(self, now):
        return not self.ever or _elapsed(now, self.last) >= self.timeout


def select_led(flame_shown, linux_silent, requested):
    if flame_shown:
        return LED_FLAME
    if linux_silent:
        return LED_LINUX_SILENT
    if requested in (LED_NORMAL, LED_SMOKE_PENDING, LED_DEGRADED, LED_FLAME):
        return requested
    return LED_DEGRADED
