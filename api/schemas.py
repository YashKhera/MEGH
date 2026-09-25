"""MEGH API schemas — TRD §7 POST /predict."""
from pydantic import BaseModel

class Next6h(BaseModel):
    lat: float
    lon: float

class PredictResponse(BaseModel):
    storm_detected: bool
    intensity_class: str = ""
    confidence: float = 0.0
    wind_kts: float = 0.0
    next_6h: Next6h | None = None
    uncertainty_km: float = 0.0
