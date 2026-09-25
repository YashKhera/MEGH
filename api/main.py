"""MEGH FastAPI entrypoint — TRD §7."""
from fastapi import FastAPI

app = FastAPI(title="MEGH — Meteorological & Environmental Geospatial Hub")

@app.get("/health")
def health():
    return {"status": "ok", "system": "MEGH"}

# TODO: POST /predict, GET /storms, GET /storm/{id}, POST /explain
# Numbers must come from ML models, not LLM (see 03_SYSTEM_ARCHITECTURE.md).
