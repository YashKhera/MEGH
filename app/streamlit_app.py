"""MEGH dashboard entrypoint."""
import streamlit as st

st.set_page_config(page_title="MEGH", layout="wide")
st.title("MEGH — Meteorological & Environmental Geospatial Hub")
st.caption("Research/demo prototype. Not an operational warning system.")
st.info("Select a historical storm to begin. See 01_PRD.md user journey.")
# TODO: satellite_view, track_map, metrics, explanation components
