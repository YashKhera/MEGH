"""Track: persistence baseline + ridge delta predictor (TRD §3/§8). Numpy only.

Features: dlat_last, dlon_last, speed, hsin, hcos, lat, lon, wind.
Target: (dlat, dlon) next 6h. Ridge closed-form on standardized feats.
Rows are plain dicts (no pandas).
"""
from __future__ import annotations
import pickle
from pathlib import Path
import numpy as np

FEATS = ["dlat_last", "dlon_last", "speed", "hsin", "hcos", "lat", "lon", "wind"]

def haversine_km(lat1, lon1, lat2, lon2) -> np.ndarray:
    R = 6371.0
    la1, la2 = np.radians(np.asarray(lat1, float)), np.radians(np.asarray(lat2, float))
    dphi = np.radians(np.asarray(lat2, float) - np.asarray(lat1, float))
    dl = np.radians(np.asarray(lon2, float) - np.asarray(lon1, float))
    a = np.sin(dphi / 2) ** 2 + np.cos(la1) * np.cos(la2) * np.sin(dl / 2) ** 2
    return 2 * R * np.arcsin(np.sqrt(np.clip(a, 0, 1)))

def build_track_rows(fixes: list[dict]) -> list[dict]:
    """fixes: dataset.csv rows. Returns supervised pairs needing prev+next fix."""
    by: dict[str, list[dict]] = {}
    for r in fixes:
        by.setdefault(r["storm_id"], []).append(r)
    rows = []
    for sid, g in by.items():
        g = sorted(g, key=lambda r: r["timestamp"])
        for i in range(1, len(g) - 1):
            p, c, n = g[i - 1], g[i], g[i + 1]
            plat, plon = float(p["latitude"]), float(p["longitude"])
            clat, clon = float(c["latitude"]), float(c["longitude"])
            nlat, nlon = float(n["latitude"]), float(n["longitude"])
            dlat_last, dlon_last = clat - plat, clon - plon
            speed = float(np.hypot(dlat_last, dlon_last))
            h = float(np.arctan2(dlon_last, dlat_last))
            rows.append({"storm_id": sid, "timestamp": c["timestamp"], "split": c["split"],
                         "lat": clat, "lon": clon, "wind": float(c["wind_kts"]),
                         "dlat_last": dlat_last, "dlon_last": dlon_last, "speed": speed,
                         "hsin": float(np.sin(h)), "hcos": float(np.cos(h)),
                         "dlat_next": nlat - clat, "dlon_next": nlon - clon,
                         "lat_next": nlat, "lon_next": nlon})
    return rows

def _design(rows: list[dict]):
    X = np.array([[r[f] for f in FEATS] for r in rows], float)
    Y = np.array([[r["dlat_next"], r["dlon_next"]] for r in rows], float)
    return X, Y

def train_ridge(rows: list[dict], alpha=1.0):
    X, Y = _design([r for r in rows if r["split"] == "train"])
    mu, sd = X.mean(axis=0), X.std(axis=0) + 1e-8
    Xn = (X - mu) / sd
    A = np.hstack([Xn, np.ones((len(Xn), 1))])
    W = np.linalg.solve(A.T @ A + alpha * np.eye(A.shape[1]), A.T @ Y)
    return {"W": W, "mu": mu, "sd": sd, "feats": FEATS}

def predict_next(model, lat, lon, dlat_last, dlon_last, wind):
    speed = float(np.hypot(dlat_last, dlon_last))
    h = float(np.arctan2(dlon_last, dlat_last))
    x = np.array([[dlat_last, dlon_last, speed, np.sin(h), np.cos(h), lat, lon, wind]], float)
    xn = (x - model["mu"]) / model["sd"]
    a = np.hstack([xn, np.ones((1, 1))])
    dlat, dlon = (a @ model["W"])[0]
    return float(lat + dlat), float(lon + dlon), float(dlat), float(dlon)

def persistence(lat, lon, dlat_last, dlon_last):
    return float(lat + dlat_last), float(lon + dlon_last)

def save_model(m, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        pickle.dump(m, f)

def load_model(path: Path):
    with open(path, "rb") as f:
        return pickle.load(f)
