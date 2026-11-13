"""Validated API inputs. Angles are degrees clockwise from EPSG:3067 grid north."""
from typing import Literal
from pydantic import BaseModel, Field, model_validator

class Camera(BaseModel):
    yaw: float = Field(0, ge=-180, le=180)
    tilt: float = Field(10, ge=-80, le=89, description="Positive tilts down")
    hfov: float = Field(80, ge=1, le=160)
    vfov: float = Field(50, ge=1, le=160)
    active: bool = True

def default_cameras():
    return [Camera(yaw=-70), Camera(yaw=0), Camera(yaw=70, active=False)]

class Candidate(BaseModel):
    name: str = Field("Aday", max_length=80)
    lon: float = Field(ge=23, le=27)
    lat: float = Field(ge=59, le=62)
    height: float = Field(600, ge=50, le=1000)
    heading: float = Field(0, ge=0, le=360)
    cameras: list[Camera] = Field(default_factory=default_cameras, min_length=3, max_length=3)
    resolution: Literal["coarse", "detailed"] = "coarse"
    max_range: float = Field(12000, ge=1000, le=25000)
    smoke_height: float = Field(50, ge=1, le=1000)
    earth_radius: float = Field(6371000, ge=6000000, le=9000000)
    priority: list[list[float]] | None = Field(None, max_length=200)
    reference: bool = False

    @model_validator(mode="after")
    def validate_cameras(self):
        if not self.reference and sum(c.active for c in self.cameras) > 2:
            raise ValueError("En fazla iki kamera bağlanabilir; üç kamera için referans modunu seçin.")
        if self.priority is not None:
            from shapely.geometry import Polygon
            if len(self.priority) < 3 or any(len(p) != 2 for p in self.priority):
                raise ValueError("Öncelik alanı en az üç [boylam, enlem] noktası içermeli.")
            if any(not (23 <= p[0] <= 27 and 59 <= p[1] <= 62) for p in self.priority):
                raise ValueError("Öncelik alanı bölge dışında.")
            if not Polygon(self.priority).is_valid:
                raise ValueError("Öncelik alanı geçerli bir çokgen olmalı.")
        return self

PRESETS = [
    Candidate(name="Kıyı · Haukilahti", lon=24.773, lat=60.159, heading=180),
    Candidate(name="İç kesim · Nuuksio", lon=24.557, lat=60.293, heading=20),
]
