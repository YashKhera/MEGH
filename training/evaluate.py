"""Held-out evaluation on test storms (TRD §5-6). Numpy/stdlib only.

Usage: python -m training.evaluate
Writes models/checkpoints/eval.json + eval_full.csv
"""
from __future__ import annotations
import csv
import json
from pathlib import Path
import numpy as np

try:
    from .dsutil import read_rows
except ImportError:
    from training.dsutil import read_rows
from models.features import frame_features
from models.intensity import IntensityBundle
from models import track as T

ROOT = Path(__file__).resolve().parents[1]

def macro_f1(yt, yp, labels):
    f1s = []
    for c in labels:
        tp = sum(1 for a, b in zip(yt, yp) if a == c and b == c)
        fp = sum(1 for a, b in zip(yt, yp) if a != c and b == c)
        fn = sum(1 for a, b in zip(yt, yp) if a == c and b != c)
        p = tp / (tp + fp) if tp + fp else 0.0
        r = tp / (tp + fn) if tp + fn else 0.0
        f1s.append(2 * p * r / (p + r) if p + r else 0.0)
    return sum(f1s) / len(f1s) if f1s else 0.0

def main():
    rows = read_rows(ROOT / "data" / "metadata" / "dataset.csv")
    te = [i for i, r in enumerate(rows) if r["split"] == "test"]
    tr = [i for i, r in enumerate(rows) if r["split"] == "train"]
    if not te:
        raise SystemExit("no test storms")
    Ximg = frame_features([str(ROOT / r["image_path"]) for r in rows])
    Xmeta = np.array([[float(r["latitude"]), float(r["longitude"]), float(r["wind_kts"])]
                      for r in rows], dtype=np.float32)
    X = np.hstack([Ximg, Xmeta])
    b = IntensityBundle.load(ROOT / "models" / "checkpoints" / "intensity.pkl")
    pred, conf, wind = b.predict(X[te])
    yt = [rows[i]["derived_class"] for i in te]
    yw = np.array([float(rows[i]["wind_kts"]) for i in te])
    labels = sorted({r["derived_class"] for r in rows})
    # vision-only ablation (image stats alone, centroid classifier)
    abl_pred = []
    for i in te:
        d = ((Ximg[tr] - Ximg[i]) ** 2).sum(axis=1)
        abl_pred.append(rows[tr[int(np.argmin(d))]]["derived_class"])
    pairs = T.build_track_rows(rows)
    tte = [r for r in pairs if r["split"] == "test"]
    m = T.load_model(ROOT / "models" / "checkpoints" / "track.pkl")
    em, ep = [], []
    for r in tte:
        mlat, mlon, _, _ = T.predict_next(m, r["lat"], r["lon"], r["dlat_last"], r["dlon_last"], r["wind"])
        plat, plon = T.persistence(r["lat"], r["lon"], r["dlat_last"], r["dlon_last"])
        em.append(T.haversine_km([r["lat_next"]], [r["lon_next"]], [mlat], [mlon])[0])
        ep.append(T.haversine_km([r["lat_next"]], [r["lon_next"]], [plat], [plon])[0])
    out = {
        "test_storms": sorted({rows[i]["storm_id"] for i in te}),
        "n_test_rows": len(te),
        "classification": {"macro_f1": macro_f1(yt, pred, labels),
                           "vision_only_macro_f1": macro_f1(yt, abl_pred, labels),
                           "labels": labels},
        "wind": {"mae": float(np.mean(np.abs(yw - wind))),
                 "rmse": float(np.sqrt(np.mean((yw - wind) ** 2)))},
        "track_test": {"n_pairs": len(tte),
                       "model_mean_km": float(np.mean(em)) if em else None,
                       "persist_mean_km": float(np.mean(ep)) if ep else None},
        "provenance": {"note": "SYN_PROXY until HURSAT/INSAT; storm-level split, test unseen"},
    }
    (ROOT / "models" / "checkpoints" / "eval.json").write_text(json.dumps(out, indent=2))
    with open(ROOT / "models" / "checkpoints" / "eval_full.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["true", "pred", "wind_true", "wind_pred", "conf"])
        w.writerows(zip(yt, pred, yw.tolist(), np.asarray(wind).tolist(), np.asarray(conf).tolist()))
    print(json.dumps(out, indent=2))

if __name__ == "__main__":
    main()
