"""Track map: full best-track + travelled-so-far + MEGH 6h + persistence + actual next.

Uses plotly.graph_objects only — plotly.express requires pandas, whose native
DLLs are blocked by AppControl on this box.
"""
import streamlit as st
import plotly.graph_objects as go


def _center_zoom(lats, lons):
    return dict(lat=sum(lats) / len(lats), lon=sum(lons) / len(lons)), 4


def render(fixes, idx, pred=None):
    """pred: dict(lat, lon, plat, plon, alat, alon) or None."""
    lats_all = [float(r["latitude"]) for r in fixes]
    lons_all = [float(r["longitude"]) for r in fixes]
    lats_so = [float(r["latitude"]) for r in fixes[:idx + 1]]
    lons_so = [float(r["longitude"]) for r in fixes[:idx + 1]]
    lat0, lon0 = lats_so[-1], lons_so[-1]
    center, zoom = _center_zoom(lats_all, lons_all)
    fig = go.Figure()
    fig.add_trace(go.Scattermap(lat=lats_all, lon=lons_all, mode="lines",
                                line=dict(color="gray", width=2), name="best track (full)"))
    fig.add_trace(go.Scattermap(lat=lats_so, lon=lons_so, mode="lines+markers",
                                marker=dict(size=7, color="blue"),
                                line=dict(color="blue", width=3), name="travelled"))
    if pred:
        fig.add_trace(go.Scattermap(lat=[pred["lat"]], lon=[pred["lon"]],
                                    mode="markers+text", text=["MEGH 6h"],
                                    marker=dict(size=13, color="red"), name="MEGH 6h"))
        fig.add_trace(go.Scattermap(lat=[pred["plat"]], lon=[pred["plon"]],
                                    mode="markers+text", text=["persist"],
                                    marker=dict(size=11, color="orange"), name="persistence"))
        if pred.get("alat") is not None:
            fig.add_trace(go.Scattermap(lat=[pred["alat"]], lon=[pred["alon"]],
                                        mode="markers+text", text=["actual"],
                                        marker=dict(size=13, color="green"), name="actual next"))
    fig.update_layout(map=dict(center=center, zoom=zoom),
                      margin=dict(l=0, r=0, t=30, b=0), height=420,
                      title=f"Track — fix {idx + 1}/{len(fixes)} @ {lat0:.2f}, {lon0:.2f}")
    st.plotly_chart(fig, use_container_width=True)
