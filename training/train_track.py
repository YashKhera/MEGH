"""Train 6h track ridge + persistence baseline (TRD §5). Numpy only.

Usage: python -m training.train_track
Saves: models/checkpoints/track.pkl + track_metrics.json
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np

try:
    from .dsutil import read_rows
except ImportError:
    from training.dsutil import read_rows
from models import track as T

ROOT = Path(__file__).resolve().parents[1]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/metadata/dataset.csv")
    ap.add_argument("--out", default="models/checkpoints/track.pkl")
    a = ap.parse_args()
    rows = read_rows(ROOT / a.data)
    pairs = T.build_track_rows(rows)
    if len(pairs) < 3:
        raise SystemExit("not enough fixes for track pairs (need >=3 per storm)")
    m = T.train_ridge(pairs)
    T.save_model(m, ROOT / a.out)
    res = {}
    for split in ("train", "val", "test"):
        s = [r for r in pairs if r["split"] == split]
        if not s:
            continue
        em, ep = [], []
        for r in s:
            mlat, mlon, _, _ = T.predict_next(m, r["lat"], r["lon"], r["dlat_last"], r["dlon_last"], r["wind"])
            plat, plon = T.persistence(r["lat"], r["lon"], r["dlat_last"], r["dlon_last"])
            em.append(T.haversine_km([r["lat_next"]], [r["lon_next"]], [mlat], [mlon])[0])
            ep.append(T.haversine_km([r["lat_next"]], [r["lon_next"]], [plat], [plon])[0])
        res[split] = {"n": len(s), "model_km": float(np.mean(em)),
                      "persist_km": float(np.mean(ep)),
                      "skill_vs_persist": float(np.mean(ep) - np.mean(em))}
    (ROOT / "models" / "checkpoints" / "track_metrics.json").write_text(json.dumps(res, indent=2))
    print(json.dumps(res, indent=2))

if __name__ == "__main__":
    main()
