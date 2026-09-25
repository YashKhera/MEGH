"""Day-1 smoke: dataset + checkpoints + API predict (storm-level, no leakage)."""
from pathlib import Path
import csv
import json

ROOT = Path(__file__).resolve().parents[1]

def test_dataset_exists():
    p = ROOT / "data" / "metadata" / "dataset.csv"
    assert p.exists(), "run training.prepare_dataset first"
    with open(p, newline="") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) > 10
    splits = {r["split"] for r in rows}
    assert {"train", "test"} <= splits
    tr = {r["storm_id"] for r in rows if r["split"] == "train"}
    te = {r["storm_id"] for r in rows if r["split"] == "test"}
    assert not (tr & te), "storm leakage!"

def test_checkpoints():
    for f in ("intensity.pkl", "track.pkl", "eval.json"):
        assert (ROOT / "models" / "checkpoints" / f).exists(), f"missing {f}"
    ev = json.loads((ROOT / "models" / "checkpoints" / "eval.json").read_text())
    assert ev["n_test_rows"] > 0

def test_api_predict():
    from fastapi.testclient import TestClient
    from api.main import app
    c = TestClient(app)
    assert c.get("/health").status_code == 200
    storms = c.get("/storms").json()["storms"]
    assert storms
    r = c.post("/predict", json={"storm_id": storms[0]["storm_id"]})
    assert r.status_code == 200
    body = r.json()
    assert body["storm_detected"] and "next_6h" in body
