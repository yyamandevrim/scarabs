"""Single-file configuration, resolved relative to the config file."""
from dataclasses import dataclass, field
from pathlib import Path
import tomllib
from .mcu_protocol import McuConfig

SLOTS = ("left", "centre", "right")

@dataclass
class CameraConfig:
    name: str
    source: str
    active: bool = True
    kind: str = "file"
    yaw: float = 0
    tilt: float = 0
    hfov: float = 80
    vfov: float = 50
    width: int = 1280
    height: int = 720
    loop: bool = True

@dataclass
class Config:
    cameras: list[CameraConfig]
    model: Path
    data_dir: Path
    analysis_hz: float = 1
    input_size: int = 640
    confidence: float = .35
    nms_iou: float = .45
    similarity_iou: float = .25
    event_timeout: float = 12
    retry_seconds: float = 2
    stale_seconds: float = 3
    retention_days: float = 7
    pre_seconds: float = 4
    post_seconds: float = 4
    clip_fps: float = 5
    clip_width: int = 640
    ort_threads: int = 2
    led_path: str | None = None
    mcu: McuConfig = field(default_factory=McuConfig)

    def __post_init__(self):
        if sorted(c.name for c in self.cameras) != sorted(SLOTS):
            raise ValueError("Configure exactly three named slots: left, centre, right")
        if sum(c.active for c in self.cameras) > 2:
            raise ValueError("At most two camera slots may be active; the board has two usable inputs")
        for c in self.cameras:
            if not isinstance(c.active, bool):
                raise ValueError(f"{c.name}: active must be true or false")
            if c.kind not in ("file", "usb") or not isinstance(c.source, str):
                raise ValueError(f"{c.name}: source must be a string; kind must be file or usb")
            if c.kind == "usb" and not c.source.startswith(("/dev/v4l/by-path/", "/dev/v4l/by-id/")):
                raise ValueError(f"{c.name}: USB source must use /dev/v4l/by-path/ or /dev/v4l/by-id/, never an index")
            if c.width <= 0 or c.height <= 0 or not 0 < c.hfov <= 180 or not 0 < c.vfov <= 180:
                raise ValueError(f"{c.name}: invalid resolution or FOV")
        if self.analysis_hz <= 0 or self.input_size < 32 or self.input_size % 32:
            raise ValueError("analysis_hz must be positive; input_size must be a positive multiple of 32")
        if not 0 < self.confidence <= 1 or not 0 < self.similarity_iou <= 1 or not 0 < self.nms_iou <= 1:
            raise ValueError("confidence and IoU thresholds must be in (0, 1]")
        if min(self.event_timeout, self.retry_seconds, self.stale_seconds, self.retention_days, self.clip_fps, self.clip_width, self.ort_threads) <= 0:
            raise ValueError("Timeouts, retention, clip dimensions/rate and ort_threads must be positive")
        if min(self.pre_seconds, self.post_seconds) < 0:
            raise ValueError("Clip durations cannot be negative")


def load_config(path: str | Path) -> Config:
    path = Path(path).resolve()
    with path.open("rb") as f:
        raw = tomllib.load(f)
    base = path.parent
    options = raw.get("station", {})
    options["model"] = (base / options.get("model", "models/smoke.onnx")).resolve()
    options["data_dir"] = (base / options.get("data_dir", "data")).resolve()
    cameras = []
    for name, values in raw.get("cameras", {}).items():
        camera = CameraConfig(name=name, **values)
        if camera.kind == "file":
            camera.source = str((base / camera.source).resolve())
        cameras.append(camera)
    options["mcu"] = McuConfig(**raw.get("mcu", {}))
    return Config(cameras=cameras, **options)
