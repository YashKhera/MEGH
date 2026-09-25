"""Shared CSV dataset helpers — stdlib only (pandas blocked by AppControl on this box)."""
from __future__ import annotations
import csv
from pathlib import Path

COLS = ["storm_id", "storm_name", "basin", "timestamp", "satellite_source",
        "image_path", "channels", "latitude", "longitude", "wind_kts",
        "pressure_hpa", "agency_status", "derived_class", "split"]

def read_rows(path: Path) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def write_rows(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        w.writerows(rows)
