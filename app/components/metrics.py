"""Metric cards: prediction, confidence bar, per-fix error, storm averages."""
import streamlit as st

def render(cls, conf, wind, bt_wind, err_m, err_p, storm_avg=None):
    m1, m2, m3 = st.columns(3)
    m1.metric("Intensity (ML)", cls, f"confidence {conf:.2f}")
    m2.metric("Wind (ML)", f"{wind:.1f} kt", f"best-track {bt_wind} kt")
    if err_m is not None:
        m3.metric("Track err (this fix)", f"{err_m:.1f} km", f"persistence {err_p:.1f} km",
                  delta_color="inverse")
    else:
        m3.metric("Track err", "—", "last fix: no next yet")
    st.progress(min(max(float(conf), 0.0), 1.0), text=f"Model confidence {conf:.0%}")
    if storm_avg:
        st.caption(f"Storm average so far — model {storm_avg['model']:.1f} km vs "
                   f"persistence {storm_avg['persist']:.1f} km "
                   f"(skill {storm_avg['persist'] - storm_avg['model']:+.1f} km, n={storm_avg['n']})")
