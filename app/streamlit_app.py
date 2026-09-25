"""MEGH dashboard Day-2: replay + viewer + map + intensity timeline + metrics.

PRD journey: storm -> frame -> prediction -> actual-vs-predicted -> why.
Backends: Local checkpoints (default) or FastAPI (http://127.0.0.1:8000).
Case study: DEMO014 (best track skill +13.5 km over persistence on test).
"""
import csv
import time
from pathlib import Path
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

from components.satellite_view import render as render_sat
from components.track_map import render as render_map
from components.metrics import render as render_metrics
from components.explanation import render as render_expl

ROOT = Path(__file__).resolve().parents[1]
CASE_STUDY = "DEMO014"

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

# ---------- sidebar ----------
splits = sorted({r["split"] for r in rows})
fsplit = st.sidebar.multiselect("Split", splits, default=splits)
storms = sorted({r["storm_id"] for r in rows if r["split"] in fsplit} or
                {r["storm_id"] for r in rows})
if st.sidebar.button(f"⭐ Load case study ({CASE_STUDY})"):
    st.session_state["sid"] = CASE_STUDY
sid = st.sidebar.selectbox("Historical storm", storms,
                           index=storms.index(st.session_state.get("sid", storms[0]))
                           if st.session_state.get("sid", storms[0]) in storms else 0)
st.session_state["sid"] = sid
s = [r for r in rows if r["storm_id"] == sid]

backend = st.sidebar.radio("Prediction backend", ["Local checkpoints", "FastAPI :8000"],
                           help="FastAPI needs: uvicorn api.main:app --reload")
play = st.sidebar.checkbox("▶ Replay storm (auto-advance)", value=False)
speed = st.sidebar.slider("Replay delay (s)", 0.3, 2.0, 0.8)
if "obs_idx" not in st.session_state or st.session_state.get("sid_prev") != sid:
    st.session_state["obs_idx"] = len(s) - 1
    st.session_state["sid_prev"] = sid
idx = st.sidebar.slider("Observation", 0, len(s) - 1, st.session_state["obs_idx"])
st.session_state["obs_idx"] = idx
row = s[idx]

# ---------- prediction ----------
pred_err = None
try:
    import numpy as np
    from models import track as T
    if backend == "Local checkpoints":
        from models.features import frame_features
        from models.intensity import IntensityBundle
        Xi = np.hstack([frame_features([str(ROOT / row["image_path"])]),
                        np.array([[float(row["latitude"]), float(row["longitude"]),
                                   float(row["wind_kts"])]], dtype=np.float32)])
        cls, conf, wind = IntensityBundle.load(
            ROOT / "models" / "checkpoints" / "intensity.pkl").predict(Xi)
        cls, conf, wind = cls[0], float(conf[0]), float(wind[0])
        m = T.load_model(ROOT / "models" / "checkpoints" / "track.pkl")
        d = _d = None
        if idx >= 1:
            dlat = float(s[idx]["latitude"]) - float(s[idx - 1]["latitude"])
            dlon = float(s[idx]["longitude"]) - float(s[idx - 1]["longitude"])
        else:
            dlat, dlon = 0.3, -0.2
        mlat, mlon, _, _ = T.predict_next(m, float(row["latitude"]), float(row["longitude"]),
                                          dlat, dlon, wind)
        plat, plon = T.persistence(float(row["latitude"]), float(row["longitude"]), dlat, dlon)
        unc = float(T.haversine_km([mlat], [mlon], [plat], [plon])[0])
        src = "local"
    else:
        import requests
        r = requests.post("http://127.0.0.1:8000/predict", json={"storm_id": sid,
                          "timestamp": row["timestamp"]}, timeout=10).json()
        cls, conf, wind = r["class"], float(r["confidence"]), float(r["wind_kts"])
        mlat, mlon = r["next_6h"]["lat"], r["next_6h"]["lon"]
        plat, plon = r["persistence_6h"]["lat"], r["persistence_6h"]["lon"]
        unc = float(r["uncertainty_km"])
        src = "api"
except FileNotFoundError as e:
    st.warning(f"Checkpoints missing ({e}). Train: train_classifier + train_track.")
    st.stop()
except Exception as e:
    st.exception(e)
    st.stop()

has_next = idx + 1 < len(s)
err_m = err_p = alat = alon = None
if has_next:
    nxt = s[idx + 1]
    alat, alon = float(nxt["latitude"]), float(nxt["longitude"])
    err_m = float(T.haversine_km([alat], [alon], [mlat], [mlon])[0])
    err_p = float(T.haversine_km([alat], [alon], [plat], [plon])[0])

# storm-average error up to current fix
import numpy as _np
try:
    from models import track as _T
    _m = _T.load_model(ROOT / "models" / "checkpoints" / "track.pkl")
    ems, eps = [], []
    for j in range(1, min(idx + 1, len(s) - 1)):
        a, b, c = s[j - 1], s[j], s[j + 1]
        dl1, dl2 = float(b["latitude"]) - float(a["latitude"]), float(b["longitude"]) - float(a["longitude"])
        qlat, qlon, _, _ = _T.predict_next(_m, float(b["latitude"]), float(b["longitude"]),
                                           dl1, dl2, float(b["wind_kts"]))
        qplat, qplon = _T.persistence(float(b["latitude"]), float(b["longitude"]), dl1, dl2)
        ems.append(float(_T.haversine_km([c["latitude"]], [c["longitude"]], [qlat], [qlon])[0]))
        eps.append(float(_T.haversine_km([c["latitude"]], [c["longitude"]], [qplat], [qplon])[0]))
    storm_avg = {"model": float(_np.mean(ems)), "persist": float(_np.mean(eps)),
                 "n": len(ems)} if ems else None
except Exception:
    storm_avg = None

# ---------- layout ----------
st.header(f"{sid} · {row['storm_name']} · best-track: {row['derived_class']}")
st.write(f"{row['timestamp']} · {float(row['latitude']):.2f}, {float(row['longitude']):.2f} · "
         f"{row['wind_kts']} kt · {row['satellite_source']} · split={row['split']} · via {src} · "
         f"uncertainty {unc:.1f} km")

top = st.columns([1, 1.4])
with top[0]:
    render_sat(row, s, idx, ROOT)
with top[1]:
    render_metrics(cls, conf, wind, row["wind_kts"], err_m, err_p, storm_avg)
    if has_next:
        st.write(f"Next 6h — model **{mlat:.3f}, {mlon:.3f}** · persistence {plat:.3f}, {plon:.3f} · "
                 f"actual **{alat:.3f}, {alon:.3f}**")
    else:
        st.write(f"Next 6h — model **{mlat:.3f}, {mlon:.3f}** · persistence {plat:.3f}, {plon:.3f} "
                 "(last fix: no ground truth yet)")

st.subheader("Track replay — travelled vs full best-track vs prediction")
render_map(s, idx, {"lat": mlat, "lon": mlon, "plat": plat, "plon": plon,
                    "alat": alat, "alon": alon})

st.subheader("Intensity timeline")
winds = [float(r["wind_kts"]) for r in s]
times = [r["timestamp"][:16] for r in s]
fig2 = go.Figure()
fig2.add_trace(go.Scatter(x=list(range(len(s))), y=winds, mode="lines+markers",
                          name="best-track wind (kt)", line=dict(color="blue")))
fig2.add_trace(go.Scatter(x=[idx], y=[winds[idx]], mode="markers",
                          marker=dict(size=14, color="black"), name="current fix"))
fig2.add_trace(go.Scatter(x=[idx + 0.5 if has_next else idx], y=[wind],
                          mode="markers+text", text=[f"ML {wind:.0f}kt"],
                          marker=dict(size=12, color="red"), name="ML wind now"))
fig2.update_layout(height=300, margin=dict(l=0, r=0, t=30, b=0),
                   xaxis_title="fix (6-hourly)", yaxis_title="kt")
st.plotly_chart(fig2, use_container_width=True)

render_expl()

with st.expander("Evaluation (held-out test storms)"):
    for f in ("eval.json", "intensity_metrics.json", "track_metrics.json"):
        p = ROOT / "models" / "checkpoints" / f
        if p.exists():
            st.code(f"--- {f} ---\n{p.read_text()[:3000]}", language="json")

# ---------- replay loop ----------
if play:
    if idx < len(s) - 1:
        time.sleep(speed)
        st.session_state["obs_idx"] = idx + 1
        st.rerun()
    else:
        st.sidebar.success("Replay finished — at last fix.")
