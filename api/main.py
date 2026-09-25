"""MEGH API — FastAPI backend for the MEGH web app.

Routes: /health, /storms, /storm/{id}, /predict, /explain (TRD §7).
Numbers always come from ML checkpoints (torch preferred, numpy fallback) —
never from the LLM. CORS enabled for the Vite dev server (see MEGH_CORS_ORIGINS).
"""
from __future__ import annotations
import csv
from datetime import datetime
from functools import lru_cache
from pathlib import Path
import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from api import config as C
from api.services.predict import get_predictors
from api.services import rag_service
from models import track as T

ROOT = Path(__file__).resolve().parents[1]
app = FastAPI(title=C.APP_TITLE, version=C.APP_VERSION)
app.add_middleware(CORSMiddleware, allow_origins=C.CORS_ORIGINS,
                   allow_methods=["*"], allow_headers=["*"])
_frames = ROOT / "data" / "processed" / "frames"
_frames.mkdir(parents=True, exist_ok=True)
app.mount("/frames", StaticFiles(directory=_frames), name="frames")

class PredictIn(BaseModel):
    storm_id: str
    timestamp: str | None = None
    dlat_last: float | None = None
    dlon_last: float | None = None

class ExplainIn(BaseModel):
    question: str
    storm_id: str | None = None
    prediction: dict | None = None

def _parse_ts(v: str) -> datetime:
    return datetime.fromisoformat(v.replace("Z", "+00:00"))

@lru_cache
def _data() -> list[dict]:
    if not C.DATASET_CSV.exists():
        raise RuntimeError("dataset.csv missing — run training.prepare_dataset")
    with open(C.DATASET_CSV, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return sorted(rows, key=lambda r: (r["storm_id"], r["timestamp"]))

def summarize(s: list[dict]) -> dict:
    winds = [float(r["wind_kts"]) for r in s]
    peak = max(winds)
    # lifecycle: first class -> peak class
    pi = int(np.argmax(winds))
    return {"storm_id": s[0]["storm_id"], "name": s[0]["storm_name"] or s[0]["storm_id"],
            "basin": s[0]["basin"], "split": s[0]["split"], "n_fixes": len(s),
            "start": s[0]["timestamp"], "end": s[-1]["timestamp"],
            "genesis_lat": float(s[0]["latitude"]), "genesis_lon": float(s[0]["longitude"]),
            "peak_wind_kts": round(peak, 1),
            "peak_class": s[pi]["derived_class"],
            "peak_lat": float(s[pi]["latitude"]), "peak_lon": float(s[pi]["longitude"]),
            "current_class": s[-1]["derived_class"],
            "source": s[0]["satellite_source"]}

@app.get("/health")
def health():
    return {"status": "ok", "system": "MEGH", "version": C.APP_VERSION,
            "ml_backend": get_predictors().backend}

@app.get("/storms")
def storms():
    rows = _data()
    by: dict[str, list[dict]] = {}
    for r in rows:
        by.setdefault(r["storm_id"], []).append(r)
    return {"storms": [summarize(sorted(v, key=lambda r: r["timestamp"]))
                       for v in by.values()]}

@app.get("/storm/{storm_id}")
def storm(storm_id: str):
    s = sorted([r for r in _data() if r["storm_id"] == storm_id],
               key=lambda r: r["timestamp"])
    if not s:
        raise HTTPException(404, "unknown storm_id")
    return {"summary": summarize(s), "fixes": s}

@app.post("/predict")
def predict(inp: PredictIn):
    s = sorted([r for r in _data() if r["storm_id"] == inp.storm_id],
               key=lambda r: r["timestamp"])
    if not s:
        raise HTTPException(404, "unknown storm_id")
    if inp.timestamp:
        q = _parse_ts(inp.timestamp)
        row = min(s, key=lambda r: abs((_parse_ts(r["timestamp"]) - q).total_seconds()))
    else:
        row = s[-1]
    P = get_predictors()
    Xi = P.features(str(ROOT / row["image_path"]), float(row["latitude"]),
                    float(row["longitude"]), float(row["wind_kts"]))
    cls, conf, wind = P.classify(Xi, [str(ROOT / row["image_path"])])
    if inp.dlat_last is None or inp.dlon_last is None:
        i = s.index(row)
        if i >= 1:
            dlat_last = float(s[i]["latitude"]) - float(s[i - 1]["latitude"])
            dlon_last = float(s[i]["longitude"]) - float(s[i - 1]["longitude"])
        else:
            dlat_last, dlon_last = 0.3, -0.2
    else:
        dlat_last, dlon_last = inp.dlat_last, inp.dlon_last
    mlat, mlon, _, _ = P.track_next(float(row["latitude"]), float(row["longitude"]),
                                    dlat_last, dlon_last, float(wind[0]))
    plat, plon = T.persistence(float(row["latitude"]), float(row["longitude"]),
                               dlat_last, dlon_last)
    unc = float(T.haversine_km([mlat], [mlon], [plat], [plon])[0])
    return {"storm_detected": True, "class": cls[0], "confidence": float(conf[0]),
            "wind_kts": float(wind[0]), "ml_backend": P.backend,
            "next_6h": {"lat": round(mlat, 3), "lon": round(mlon, 3)},
            "persistence_6h": {"lat": round(plat, 3), "lon": round(plon, 3)},
            "uncertainty_km": round(unc, 1),
            "input_fix": {"lat": float(row["latitude"]), "lon": float(row["longitude"]),
                          "timestamp": row["timestamp"], "image": row["image_path"],
                          "source": row["satellite_source"]}}

@app.post("/explain")
def explain(inp: ExplainIn):
    return rag_service.explain(inp.question, inp.prediction or {})

@app.get("/metrics")
def metrics():
    """Held-out evaluation + model info for dashboards (dynamic, from checkpoints)."""
    import json
    out: dict = {"ml_backend": get_predictors().backend}
    for f in ("eval.json", "intensity_metrics.json", "track_metrics.json"):
        p = C.CKPT_DIR / f
        if p.exists():
            try:
                out[f.replace(".json", "")] = json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                pass
    return out

# ---- serve the React build (single-port org site: UI + API together) ----
_DIST = ROOT / "web" / "dist"
if _DIST.exists():
    from fastapi.responses import FileResponse
    app.mount("/assets", StaticFiles(directory=_DIST / "assets"), name="assets")

    @app.get("/{path:path}")
    def spa(path: str):
        if path.startswith(("health", "storms", "storm", "predict", "explain",
                             "frames", "metrics", "docs", "openapi", "assets")):
            raise HTTPException(404, "unknown path")
        cand = _DIST / path
        if path and cand.is_file():
            return FileResponse(cand)
        return FileResponse(_DIST / "index.html")
