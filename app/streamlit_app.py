"""MEGH dashboard — PRD journey: storm -> frame -> prediction -> actual vs predicted."""
import csv
import json
from pathlib import Path
import streamlit as st
import plotly.express as px
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
st.set_page_config(page_title="MEGH", layout="wide")
st.title("MEGH — Meteorological & Environmental Geospatial Hub")
st.caption("Research/demo prototype. Not an operational warning system.")

meta = ROOT / "data" / "metadata" / "dataset.csv"
if not meta.exists():
    st.error("No dataset.csv — run: python -m training.prepare_dataset --synthetic-fallback")
    st.stop()
with open(meta, newline="", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))
rows.sort(key=lambda r: (r["storm_id"], r["timestamp"]))
storms = sorted({r["storm_id"] for r in rows})
sid = st.sidebar.selectbox("Historical storm", storms)
s = [r for r in rows if r["storm_id"] == sid]
idx = st.sidebar.slider("Observation", 0, len(s) - 1, len(s) - 1)
row = s[idx]

c1, c2 = st.columns([1, 1.2])
with c1:
    st.subheader(f"{sid} · {row['storm_name']} · {row['derived_class']}")
    st.write(f"{row['timestamp']} · {float(row['latitude']):.2f}, {float(row['longitude']):.2f} · "
             f"{row['wind_kts']} kt · {row['satellite_source']} · split={row['split']}")
    img = ROOT / row["image_path"]
    if img.exists():
        st.image(Image.open(img).resize((256, 256)), caption=row["image_path"])
try:
    import numpy as np
    from models.features import frame_features
    from models.intensity import IntensityBundle
    from models import track as T
    Xi = np.hstack([frame_features([str(ROOT / row["image_path"])]),
                    np.array([[float(row["latitude"]), float(row["longitude"]),
                               float(row["wind_kts"])]], dtype=np.float32)])
    b = IntensityBundle.load(ROOT / "models" / "checkpoints" / "intensity.pkl")
    cls, conf, wind = b.predict(Xi)
    m = T.load_model(ROOT / "models" / "checkpoints" / "track.pkl")
    if idx >= 1:
        dlat = float(s[idx]["latitude"]) - float(s[idx - 1]["latitude"])
        dlon = float(s[idx]["longitude"]) - float(s[idx - 1]["longitude"])
    else:
        dlat, dlon = 0.3, -0.2
    mlat, mlon, _, _ = T.predict_next(m, float(row["latitude"]), float(row["longitude"]),
                                      dlat, dlon, float(wind[0]))
    plat, plon = T.persistence(float(row["latitude"]), float(row["longitude"]), dlat, dlon)
    with c2:
        st.subheader("MEGH prediction (ML)")
        st.metric("Intensity", cls[0], f"conf {float(conf[0]):.2f}")
        st.metric("Wind", f"{float(wind[0]):.1f} kt", f"best-track {row['wind_kts']} kt")
        st.write(f"Next 6h (model): **{mlat:.3f}, {mlon:.3f}** · persistence: {plat:.3f}, {plon:.3f}")
        if idx + 1 < len(s):
            nxt = s[idx + 1]
            err_m = float(T.haversine_km([nxt["latitude"]], [nxt["longitude"]], [mlat], [mlon])[0])
            err_p = float(T.haversine_km([nxt["latitude"]], [nxt["longitude"]], [plat], [plon])[0])
            st.write(f"Actual next: **{float(nxt['latitude']):.3f}, {float(nxt['longitude']):.3f}** · "
                     f"model err **{err_m:.1f} km** vs persistence **{err_p:.1f} km**")
            lats = [float(r["latitude"]) for r in s[:idx + 2]]
            lons = [float(r["longitude"]) for r in s[:idx + 2]]
        else:
            lats = [float(r["latitude"]) for r in s]
            lons = [float(r["longitude"]) for r in s]
        fig = px.line_map(lat=lats, lon=lons, zoom=4, height=380)
        fig.add_scattermap(lat=[mlat], lon=[mlon], mode="markers+text", text=["MEGH 6h"],
                           marker=dict(size=12, color="red"), name="MEGH 6h")
        if idx + 1 < len(s):
            fig.add_scattermap(lat=[float(s[idx+1]["latitude"])], lon=[float(s[idx+1]["longitude"])],
                               mode="markers+text", text=["actual"],
                               marker=dict(size=12, color="green"), name="actual")
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Numbers from ML checkpoints — LLM does not generate them (TRD boundary).")
except FileNotFoundError as e:
    with c2:
        st.warning(f"Checkpoints missing ({e}). Train: train_classifier + train_track.")
except Exception as e:
    with c2:
        st.exception(e)

with st.expander("Evaluation (test storms)"):
    for f in ("eval.json", "intensity_metrics.json", "track_metrics.json"):
        p = ROOT / "models" / "checkpoints" / f
        if p.exists():
            st.code(f"--- {f} ---\n{p.read_text()[:3000]}", language="json")
