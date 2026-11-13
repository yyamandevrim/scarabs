"""Shared constants for the station <-> UNO Q microcontroller bridge.

Must match firmware/acorn_mcu/acorn_logic.h and acorn_mcu.ino.
"""
from dataclasses import dataclass

PROTOCOL_VERSION = 1
READING_METHOD = "acorn_reading"  # MCU -> Linux, Bridge.notify
STATE_METHOD = "acorn_state"      # Linux -> MCU, request (state, seq) -> protocol version
DEFAULT_SOCKET = "/var/run/arduino-router.sock"

# Positional fields of Bridge.notify("acorn_reading", ...).
READING_FIELDS = ("protocol", "seq", "uptime_ms", "raw", "smoothed_raw", "level_permille",
                  "adc_bits", "digital_active", "triggered", "led", "linux_ok")

LED_BOOT, LED_NORMAL, LED_SMOKE_PENDING, LED_DEGRADED, LED_FLAME, LED_LINUX_SILENT = range(6)

# One table for the whole LED scheme: colour plus a distinct rhythm per state.
LED_STATES = {
    LED_BOOT: {"name": "boot", "colour": "red→green→blue", "pattern": "one 0.75 s lamp test at power-up",
               "text": "Başlatılıyor"},
    LED_NORMAL: {"name": "normal", "colour": "green", "pattern": "steady",
                 "text": "Normal gözlem"},
    LED_SMOKE_PENDING: {"name": "smoke_pending", "colour": "amber", "pattern": "double blink every 1.2 s",
                        "text": "Duman şüphesi operatör kararı bekliyor"},
    LED_DEGRADED: {"name": "degraded", "colour": "blue", "pattern": "slow blink, 1 s on / 1 s off",
                   "text": "Gözlem kapsamı azaldı"},
    LED_FLAME: {"name": "flame_sensor", "colour": "red", "pattern": "fast blink, 5 per second",
                "text": "Alev sensörü tetiklendi"},
    LED_LINUX_SILENT: {"name": "linux_silent", "colour": "blue", "pattern": "short flash every 2 s",
                       "text": "İstasyon yazılımı yanıt vermiyor"},
}

FLAME_TRIGGERED_TEXT = "Alev sensörü tetiklendi"
FLAME_SCOPE_NOTE = ("İstasyondaki yerel kızılötesi alev sensörü (KY-026): yalnızca yaklaşık bir metre içindeki "
                    "açık alevi algılar, güneş ışığı ve diğer kızılötesi kaynaklarla tetiklenebilir. "
                    "Uzaktan orman yangını tespiti yapmaz ve kamera duman şüphesini doğrulamaz.")


def led_info(code):
    if code is None:
        return None
    info = LED_STATES.get(code, {"name": "unknown", "colour": None, "pattern": None, "text": "Bilinmiyor"})
    return {"code": code, **info}


@dataclass
class McuConfig:
    # off: no microcontroller; simulated: in-process model of the firmware
    # (demo without hardware, clearly marked simulated); router: the real
    # board through arduino-router's Unix socket.
    mode: str = "off"
    socket: str = DEFAULT_SOCKET
    state_interval: float = 1.0    # seconds between state messages (heartbeat)
    reading_timeout: float = 3.0   # no reading for this long = sensor disconnected
    request_timeout: float = 2.0   # unanswered state request = MCU not acknowledging
    reconnect_seconds: float = 2.0

    def __post_init__(self):
        if self.mode not in ("off", "simulated", "router"):
            raise ValueError("mcu.mode must be off, simulated or router")
        if min(self.state_interval, self.reading_timeout, self.request_timeout, self.reconnect_seconds) <= 0:
            raise ValueError("mcu intervals and timeouts must be positive")
        if self.reading_timeout <= self.state_interval / 2:
            raise ValueError("mcu.reading_timeout is too short")


def parse_reading(params):
    """Validate one acorn_reading notification; raise ValueError if malformed."""
    if not isinstance(params, (list, tuple)) or len(params) < len(READING_FIELDS):
        raise ValueError("acorn_reading: unexpected parameter count")
    reading = dict(zip(READING_FIELDS, params))
    if reading["protocol"] != PROTOCOL_VERSION:
        raise ValueError(f"acorn_reading: protocol {reading['protocol']!r}, expected {PROTOCOL_VERSION}")
    for key in ("seq", "uptime_ms", "raw", "smoothed_raw", "level_permille", "adc_bits", "led"):
        if not isinstance(reading[key], int) or isinstance(reading[key], bool):
            raise ValueError(f"acorn_reading: {key} must be an integer")
    for key in ("digital_active", "triggered", "linux_ok"):
        if not isinstance(reading[key], bool):
            raise ValueError(f"acorn_reading: {key} must be a boolean")
    if not 0 <= reading["level_permille"] <= 1000 or not 8 <= reading["adc_bits"] <= 16:
        raise ValueError("acorn_reading: value out of range")
    return reading
