"""MEGH backend settings — everything env-driven, no hardcoded hosts/ports."""
from __future__ import annotations
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DATASET_CSV = Path(os.getenv("MEGH_DATASET", str(ROOT / "data" / "metadata" / "dataset.csv")))
CKPT_DIR = Path(os.getenv("MEGH_CKPT_DIR", str(ROOT / "models" / "checkpoints")))
INTENSITY_CKPT = CKPT_DIR / "intensity.pkl"
TRACK_CKPT = CKPT_DIR / "track.pkl"
# PyTorch checkpoints (preferred when present; numpy fallback otherwise)
TORCH_INTENSITY_CKPT = CKPT_DIR / "torch_intensity.pt"
TORCH_TRACK_CKPT = CKPT_DIR / "torch_track.pt"
RAG_INDEX = Path(os.getenv("MEGH_RAG_INDEX", str(ROOT / "rag" / "index.pkl")))

# LLM hook (OpenAI-compatible chat endpoint). Empty => template answers.
LLM_URL = os.getenv("MEGH_LLM_URL", "")
LLM_KEY = os.getenv("MEGH_LLM_KEY", "")
LLM_MODEL = os.getenv("MEGH_LLM_MODEL", "megh-default")

CORS_ORIGINS = [o.strip() for o in os.getenv(
    "MEGH_CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",") if o.strip()]

APP_TITLE = "MEGH API"
APP_VERSION = "0.3.0"
