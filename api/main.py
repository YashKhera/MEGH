"""MEGH FastAPI — TRD §7. Numbers from ML checkpoints, never LLM. Stdlib+numpy only."""
from __future__ import annotations
import csv
from datetime import datetime
from functools import lru_cache
from pathlib import Path
import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from models.features import frame_features
from models.intensity import IntensityBundle
from models import track as T

ROOT = Path(__file__).resolve().parents[1]
app = FastAPI(title="MEGH — Meteorological & Environmental Geospatial Hub")

class PredictIn(BaseModel):
    storm_id: str
    timestamp: str | None = None
    dlat_last: float | None = None
    dlon_last: float | None = None

def _parse_ts(v: str) -> datetime:
    return datetime.fromisoformat(v.replace("Z", "+00:00"))

@lru_cache
def _data() -> list[dict]:
    p = ROOT / "data" / "metadata" / "dataset.csv"
    if not p.exists():
        raise RuntimeError("dataset.csv missing — run training.prepare_dataset")
    with open(p, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return sorted(rows, key=lambda r: (r["storm_id"], r["timestamp"]))

@lru_cache
def _intensity():
    return IntensityBundle.load(ROOT / "models" / "checkpoints" / "intensity.pkl")

@lru_cache
def _trackm():
    return T.load_model(ROOT / "models" / "checkpoints" / "track.pkl")

@app.get("/health")
def health():
    return {"status": "ok", "system": "MEGH"}

@app.get("/storms")
def storms():
    rows = _data()
    agg: dict[str, dict] = {}
    for r in rows:
        a = agg.setdefault(r["storm_id"], {"storm_id": r["storm_id"], "name": r["storm_name"],
                                           "split": r["split"], "n": 0,
                                           "start": r["timestamp"], "end": r["timestamp"]})
        a["n"] += 1
        a["start"] = min(a["start"], r["timestamp"])
        a["end"] = max(a["end"], r["timestamp"])
    return {"storms": sorted(agg.values(), key=lambda a: a["storm_id"])}

@app.get("/storm/{storm_id}")
def storm(storm_id: str):
    s = [r for r in _data() if r["storm_id"] == storm_id]
    if not s:
        raise HTTPException(404, "unknown storm_id")
    return {"storm_id": storm_id, "fixes": s}

@app.post("/predict")
def predict(inp: PredictIn):
    s = [r for r in _data() if r["storm_id"] == inp.storm_id]
    if not s:
        raise HTTPException(404, "unknown storm_id")
    if inp.timestamp:
        q = _parse_ts(inp.timestamp)
        row = min(s, key=lambda r: abs((_parse_ts(r["timestamp"]) - q).total_seconds()))
    else:
        row = s[-1]
    Xi = np.hstack([frame_features([str(ROOT / row["image_path"])]),
                    np.array([[float(row["latitude"]), float(row["longitude"]),
                               float(row["wind_kts"])]], dtype=np.float32)])
    b = _intensity()
    cls, conf, wind = b.predict(Xi)
    if inp.dlat_last is None or inp.dlon_last is None:
        i = s.index(row)
        if i >= 1:
            dlat_last = float(s[i]["latitude"]) - float(s[i - 1]["latitude"])
            dlon_last = float(s[i]["longitude"]) - float(s[i - 1]["longitude"])
        else:
            dlat_last, dlon_last = 0.3, -0.2
    else:
        dlat_last, dlon_last = inp.dlat_last, inp.dlon_last
    m = _trackm()
    mlat, mlon, _, _ = T.predict_next(m, float(row["latitude"]), float(row["longitude"]),
                                      dlat_last, dlon_last, float(wind[0]))
    plat, plon = T.persistence(float(row["latitude"]), float(row["longitude"]), dlat_last, dlon_last)
    unc = float(T.haversine_km([mlat], [mlon], [plat], [plon])[0])
    return {"storm_detected": True, "class": cls[0], "confidence": float(conf[0]),
            "wind_kts": float(wind[0]),
            "next_6h": {"lat": round(mlat, 3), "lon": round(mlon, 3)},
            "persistence_6h": {"lat": round(plat, 3), "lon": round(plon, 3)},
            "uncertainty_km": round(unc, 1),
            "input_fix": {"lat": float(row["latitude"]), "lon": float(row["longitude"]),
                          "timestamp": row["timestamp"], "image": row["image_path"],
                          "source": row["satellite_source"]}}

class ExplainIn(BaseModel):
    question: str
    storm_id: str | None = None
    prediction: dict | None = None

@app.post("/explain")
def explain(inp: ExplainIn):
    return {"answer": ("MEGH numbers come from ML checkpoints (intensity.pkl, track.pkl); "
                       "full IMD/WMO/IBTrACS-cited RAG lands Day 3. "
                       f"Question received: {inp.question[:280]}"),
            "sources": [], "note": "RAG Day-3 stub — no LLM numbers invented."}
