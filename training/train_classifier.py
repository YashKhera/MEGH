"""Train intensity classifier + wind regressor (storm-level train split).

Usage: python -m training.train_classifier
Saves: models/checkpoints/intensity.pkl + intensity_metrics.json
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np

try:
    from .dsutil import read_rows
except ImportError:
    from training.dsutil import read_rows
from models.features import frame_features
from models.intensity import IntensityBundle

ROOT = Path(__file__).resolve().parents[1]

def macro_f1(yt, yp, labels):
    f1s = []
    for c in labels:
        tp = sum(1 for a, b in zip(yt, yp) if a == c and b == c)
        fp = sum(1 for a, b in zip(yt, yp) if a != c and b == c)
        fn = sum(1 for a, b in zip(yt, yp) if a == c and b != c)
        prec = tp / (tp + fp) if tp + fp else 0.0
        rec = tp / (tp + fn) if tp + fn else 0.0
        f1s.append(2 * prec * rec / (prec + rec) if prec + rec else 0.0)
    return sum(f1s) / len(f1s) if f1s else 0.0

def bal_acc(yt, yp, labels):
    recs = []
    for c in labels:
        tp = sum(1 for a, b in zip(yt, yp) if a == c and b == c)
        fn = sum(1 for a, b in zip(yt, yp) if a == c and b != c)
        recs.append(tp / (tp + fn) if tp + fn else 0.0)
    return sum(recs) / len(recs) if recs else 0.0

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/metadata/dataset.csv")
    ap.add_argument("--out", default="models/checkpoints/intensity.pkl")
    a = ap.parse_args()
    rows = read_rows(ROOT / a.data)
    if not rows:
        raise SystemExit("empty dataset — run prepare_dataset first")
    Ximg = frame_features([str(ROOT / r["image_path"]) for r in rows])
    Xmeta = np.array([[float(r["latitude"]), float(r["longitude"]), float(r["wind_kts"])]
                      for r in rows], dtype=np.float32)
    X = np.hstack([Ximg, Xmeta])
    tr = [i for i, r in enumerate(rows) if r["split"] == "train"]
    va = [i for i, r in enumerate(rows) if r["split"] == "val"]
    if not tr:
        raise SystemExit("no train rows")
    b = IntensityBundle().fit(X[tr], [rows[i]["derived_class"] for i in tr],
                              np.array([float(rows[i]["wind_kts"]) for i in tr]))
    b.save(ROOT / a.out)
    labels = sorted({r["derived_class"] for r in rows})
    out: dict = {"model": a.out}
    for name, idx in (("train", tr), ("val", va)):
        if not idx:
            continue
        pred, conf, wind = b.predict(X[idx])
        yt = [rows[i]["derived_class"] for i in idx]
        yw = np.array([float(rows[i]["wind_kts"]) for i in idx])
        out[name] = {"n": len(idx), "macro_f1": macro_f1(yt, pred, labels),
                     "bal_acc": bal_acc(yt, pred, labels),
                     "wind_mae": float(np.mean(np.abs(yw - wind))),
                     "wind_rmse": float(np.sqrt(np.mean((yw - wind) ** 2))),
                     "mean_conf": float(np.mean(conf))}
    (ROOT / "models" / "checkpoints" / "intensity_metrics.json").write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))

if __name__ == "__main__":
    main()
