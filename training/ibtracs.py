"""IBTrACS acquisition for MEGH (05_DATA_PLAN.md §1). Stdlib-only streaming download.

Keeps needed cols, filters basin, trims to most-recent N storms.
IBTrACS CSV is large (~GB); we stream lines and stop once enough NI SIDs seen.

Usage:
    python -m training.ibtracs --out data/raw/ibtracs_ni.csv --basin NI --max-storms 30
"""
from __future__ import annotations
import argparse
import csv
import sys
import urllib.request
from pathlib import Path

IBTRACS_URL = "https://www.ncei.noaa.gov/pub/data/circulation/ibtracs/v04r01/ibtracs.v04r01.csv"
NEEDED = ["SID", "NAME", "ISO_TIME", "LAT", "LON", "WMO_WIND", "WMO_PRES",
          "BASIN", "USA_WIND", "USA_PRES", "NEWDELHI_WIND"]

def fetch(out: Path, basin: str = "NI", max_storms: int = 30) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    print(f"[ibtracs] streaming {IBTRACS_URL} ...")
    try:
        resp = urllib.request.urlopen(IBTRACS_URL, timeout=60)
        import io
        text = io.TextIOWrapper(resp, encoding="utf-8", errors="replace")
        reader = csv.DictReader(text)
        kept: list[dict] = []
        seen_order: list[str] = []
        seen: set[str] = set()
        for r in reader:
            if basin and r.get("BASIN", "").strip() != basin:
                continue
            sid = r.get("SID", "").strip()
            if not sid or not (r.get("ISO_TIME") or "").strip():
                continue
            if sid not in seen:
                seen.add(sid)
                seen_order.append(sid)
            kept.append({k: r.get(k, "") for k in NEEDED})
            if max_storms and len(seen) >= max_storms * 4 and len(kept) > 200_000:
                break
        if max_storms:
            want = set(seen_order[-max_storms:])
            kept = [r for r in kept if r["SID"] in want]
        with open(out, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=NEEDED)
            w.writeheader()
            w.writerows(kept)
        print(f"[ibtracs] wrote {out} rows={len(kept)} storms={len({r['SID'] for r in kept})}")
    except Exception as e:
        print(f"[ibtracs] download failed: {e}", file=sys.stderr)
        raise SystemExit(2)
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/raw/ibtracs_ni.csv")
    ap.add_argument("--basin", default="NI")
    ap.add_argument("--max-storms", type=int, default=30)
    a = ap.parse_args()
    fetch(Path(a.out), a.basin, a.max_storms)

if __name__ == "__main__":
    main()
