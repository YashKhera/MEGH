# MEGH — Meteorological & Environmental Geospatial Hub

**Team:** Vittvanni | **SIH PS:** SIH26070

A Multi-Source Satellite Intelligence System for Tropical Cyclone Identification, Classification and Short-Horizon Prediction.

> Research/demo decision-support prototype. Not an operational warning system.

## Structure

See `../07_REPOSITORY.md` in MEGH_SIH26070_Docs (or `docs/` after copy) for full spec.

```
app/        Streamlit dashboard (satellite viewer, track map, metrics, explanation)
api/        FastAPI prediction + explanation service
data/       raw / processed / metadata (IBTrACS + satellite, gitignored)
models/     vision, intensity, track + checkpoints (gitignored)
training/   dataset prep, train, evaluate (storm-level splits)
rag/        ingest, retrieve, rerank, prompts + sources
notebooks/  exploration
tests/      smoke/unit tests
docs/       copy/link of spec docs
```

## Quickstart (run from this folder — `api` only imports from the repo root)

```powershell
cd D:\SIH26070\Project70\MEGH_SIH26070_Docs\MEGH
.\.venv\Scripts\python.exe -m uvicorn api.main:app --reload --port 8000
```

Frontend (second terminal):

```powershell
cd D:\SIH26070\Project70\MEGH_SIH26070_Docs\MEGH\web
npm run dev      # opens the dev server; API calls proxy to :8000
```

> `ModuleNotFoundError: No module named 'api'` means uvicorn was started from
> the wrong folder — `cd` into this folder first.

## API (TRD §7)

* `POST /predict` -> storm_detected, class, confidence, wind_kts, next_6h, uncertainty_km
* `GET /storms`, `GET /storm/{id}`, `POST /explain`

## Principles

* Numbers from ML models, not LLM.
* RAG = evidence + explanation + provenance.
* Storm-level eval, persistence baseline, visible limitations.
```

