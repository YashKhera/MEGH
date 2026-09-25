"""MEGH dataset prep: IBTrACS -> aligned metadata + storm-centred frames (05_DATA_PLAN.md).

Stdlib + numpy + Pillow only. For each best-track row: UTC normalize, drop bad
coords, derive IMD class, storm-level train/val/test split, deterministic
synthetic proxy frame (SYN_PROXY) until HURSAT/INSAT ingest lands.

Outputs: data/processed/frames/*.png + data/metadata/dataset.csv
Usage:
    python -m training.prepare_dataset --input data/raw/ibtracs_ni.csv --n-storms 20
    python -m training.prepare_dataset --synthetic-fallback
"""
from __future__ import annotations
import argparse
import csv
import hashlib
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
from PIL import Image

try:
    from .imd import wind_to_class
    from .dsutil import write_rows
except ImportError:  # script run as file
    from training.imd import wind_to_class
    from training.dsutil import write_rows

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
META = ROOT / "data" / "metadata"

def _f(v, default=float("nan")) -> float:
    try:
        f = float(str(v).strip())
        return f if np.isfinite(f) else default
    except (TypeError, ValueError):
        return default

def pick_wind(r: dict) -> float:
    for c in ("NEWDELHI_WIND", "USA_WIND", "WMO_WIND", "wind_kts"):
        v = _f(r.get(c, ""))
        if np.isfinite(v) and v >= 0:
            return v
    return float("nan")

def pick_pres(r: dict) -> float:
    for c in ("USA_PRES", "WMO_PRES", "pressure_hpa"):
        v = _f(r.get(c, ""))
        if np.isfinite(v) and v > 0:
            return v
    return float("nan")

def proxy_frame(wind_kts: float, seed_key: str, size: int = 64) -> Image.Image:
    h = int(hashlib.md5(seed_key.encode()).hexdigest()[:8], 16) % (2 ** 31)
    rng = np.random.default_rng(h)
    y, x = np.mgrid[0:size, 0:size].astype(float)
    cx = cy = (size - 1) / 2
    r = np.sqrt((x - cx) ** 2 + (y - cy) ** 2) / (size / 2)
    theta = np.arctan2(y - cy, x - cx)
    w = float(np.clip(wind_kts if np.isfinite(wind_kts) else 25.0, 10, 130))
    core = np.exp(-(r ** 2) / (0.08 + 0.35 * (1 - w / 150)))
    spiral = 0.5 + 0.5 * np.sin(3 * theta + 6 * r - w / 25)
    arm = np.exp(-r * 1.8) * spiral * 0.6
    noise = rng.normal(0, 0.06, (size, size))
    img = np.clip(0.15 + 0.7 * core + 0.35 * arm + noise, 0, 1)
    return Image.fromarray((img * 255).astype(np.uint8), mode="L")

def storm_split(sids: list[str], val_frac=0.15, test_frac=0.2, seed=7) -> dict:
    rng = np.random.default_rng(seed)
    s = sorted(set(sids))
    idx = np.arange(len(s))
    rng.shuffle(idx)
    s = [s[i] for i in idx]
    n = len(s)
    n_test = max(1, int(n * test_frac)) if n >= 3 else min(1, n)
    n_val = max(1, int(n * val_frac)) if n >= 4 else 0
    test = set(s[:n_test])
    val = set(s[n_test:n_test + n_val])
    return {sid: ("test" if sid in test else "val" if sid in val else "train") for sid in s}

def _parse_time(v: str) -> datetime | None:
    v = (v or "").strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(v)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except ValueError:
        return None

def build_from_ibtracs(src: Path, n_storms: int = 20, img_size: int = 64) -> Path:
    with open(src, newline="", encoding="utf-8") as f:
        raw = list(csv.DictReader(f))
    # normalize SID column name
    for r in raw:
        if "SID" in r and "storm_id" not in r:
            r["storm_id"] = r["SID"]
    sids = sorted({r.get("SID", "") for r in raw if r.get("SID")})[-n_storms:]
    rows = [r for r in raw if r.get("SID") in sids]
    split = storm_split(sids)
    frames = PROCESSED / "frames"
    frames.mkdir(parents=True, exist_ok=True)
    recs = []
    for r in rows:
        dt = _parse_time(r.get("ISO_TIME", ""))
        lat, lon = _f(r.get("LAT")), _f(r.get("LON"))
        w = pick_wind(r)
        if dt is None or not np.isfinite(lat) or not np.isfinite(lon) or not np.isfinite(w):
            continue
        sid = r["SID"]
        key = f"{sid}_{dt.isoformat()}"
        fn = f"{sid}_{dt.strftime('%Y%m%d%H%M')}.png"
        p = frames / fn
        if not p.exists():
            proxy_frame(w, key, img_size).save(p)
        pr = pick_pres(r)
        recs.append({"storm_id": sid, "storm_name": (r.get("NAME") or "").strip(),
                     "basin": (r.get("BASIN") or "NI").strip(), "timestamp": dt.isoformat(),
                     "satellite_source": "SYN_PROXY", "image_path": f"data/processed/frames/{fn}",
                     "channels": "IR_PROXY", "latitude": round(float(lat), 4),
                     "longitude": round(float(lon), 4), "wind_kts": round(float(w), 1),
                     "pressure_hpa": "" if not np.isfinite(pr) else round(float(pr), 1),
                     "agency_status": "", "derived_class": wind_to_class(float(w)),
                     "split": split[sid]})
    recs.sort(key=lambda r: (r["storm_id"], r["timestamp"]))
    out = META / "dataset.csv"
    write_rows(out, recs)
    print(f"[prepare] storms={len(sids)} rows={len(recs)} -> {out}")
    return out

def build_synthetic_fallback(n_storms: int = 20, steps: int = 20) -> Path:
    rng = np.random.default_rng(70)
    sids = [f"DEMO{i:03d}" for i in range(1, n_storms + 1)]
    split = storm_split(sids)
    frames = PROCESSED / "frames"
    frames.mkdir(parents=True, exist_ok=True)
    recs = []
    base = datetime(2023, 10, 1, tzinfo=timezone.utc)
    for i, sid in enumerate(sids):
        lat, lon = 8 + float(rng.uniform(0, 6)), 82 + float(rng.uniform(0, 8))
        wind = float(rng.uniform(25, 55))
        for t in range(steps):
            lat += float(rng.normal(0.35, 0.15))
            lon += float(rng.normal(-0.25, 0.2))
            wind = float(np.clip(wind + float(rng.normal(2.5, 4)), 20, 125))
            from datetime import timedelta
            ts = (base + timedelta(hours=6 * (t + i * 3))).isoformat()
            fn = f"{sid}_{t:03d}.png"
            proxy_frame(wind, f"{sid}_{t}", 64).save(frames / fn)
            recs.append({"storm_id": sid, "storm_name": f"Demo-{i+1}", "basin": "NI",
                         "timestamp": ts, "satellite_source": "SYN_PROXY",
                         "image_path": f"data/processed/frames/{fn}", "channels": "IR_PROXY",
                         "latitude": round(lat, 3), "longitude": round(lon, 3),
                         "wind_kts": round(wind, 1), "pressure_hpa": "",
                         "agency_status": "", "derived_class": wind_to_class(wind),
                         "split": split[sid]})
    out = META / "dataset.csv"
    write_rows(out, recs)
    print(f"[prepare] synthetic storms={n_storms} rows={len(recs)} -> {out}")
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default="data/raw/ibtracs_ni.csv")
    ap.add_argument("--n-storms", type=int, default=20)
    ap.add_argument("--synthetic-fallback", action="store_true")
    ap.add_argument("--synthetic-storms", type=int, default=20)
    a = ap.parse_args()
    src = Path(a.input) if Path(a.input).is_absolute() else ROOT / a.input
    if a.synthetic_fallback or not src.exists():
        if not a.synthetic_fallback:
            print(f"[prepare] {src} missing -> synthetic fallback")
        build_synthetic_fallback(a.synthetic_storms)
    else:
        build_from_ibtracs(src, a.n_storms)

if __name__ == "__main__":
    main()
