"""Validated API inputs. Angles are degrees clockwise from EPSG:3067 grid north."""
from typing import Literal
from pydantic import BaseModel, Field, model_validator, ConfigDict

class Camera(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    yaw: float = Field(0, ge=-180, le=180)
    tilt: float = Field(10, ge=-80, le=89, description="Positive tilts down")
    hfov: float = Field(80, ge=1, le=160)
    vfov: float = Field(50, ge=1, le=160)
    active: bool = True

def default_cameras():
    return [Camera(yaw=-70), Camera(yaw=0), Camera(yaw=70, active=False)]

class Candidate(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    name: str = Field("Candidate", max_length=80)
    lon: float = Field(ge=23, le=27)
    lat: float = Field(ge=59, le=62)
    height: float = Field(600, ge=10, le=1000)
    heading: float = Field(0, ge=0, le=360)
    cameras: list[Camera] = Field(default_factory=default_cameras, min_length=3, max_length=3)
    resolution: Literal["coarse", "detailed"] = "coarse"
    max_range: float = Field(12000, ge=1000, le=15000)
    smoke_height: float = Field(50, ge=1, le=1000)
    earth_radius: float = Field(6371000, ge=6000000, le=9000000)
    priority: list[list[float]] | None = Field(None, max_length=100)
    reference: bool = False

    @model_validator(mode="after")
    def validate_cameras(self):
        if not self.reference and sum(c.active for c in self.cameras) > 2:
            raise ValueError("En fazla iki kamera bağlanabilir; üç kamera için referans modunu seçin.")
        if self.priority is not None:
            from shapely.geometry import Polygon
            if len(self.priority) < 3 or any(len(p) != 2 for p in self.priority):
                raise ValueError("Priority area requires at least three [longitude, latitude] points.")
            if any(not (23 <= p[0] <= 27 and 59 <= p[1] <= 62) for p in self.priority):
                raise ValueError("Priority polygon is outside the region.")
            if not Polygon(self.priority).is_valid:
                raise ValueError("Priority area must be a valid polygon.")
            from pyproj import Transformer
            project = Transformer.from_crs(4326, 3067, always_xy=True)
            polygon = Polygon([project.transform(*p) for p in self.priority])
            if polygon.area <= 0 or polygon.area > 2_000_000_000:
                raise ValueError("Priority polygon must have positive area and be at most 2000 km².")
        return self

PRESETS = [
    Candidate(name="Coast · Haukilahti", lon=24.773, lat=60.159, heading=180),
    Candidate(name="Inland · Nuuksio", lon=24.557, lat=60.293, heading=20),
]
