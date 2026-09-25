"""Satellite viewer: current frame + prev/next filmstrip (PRD satellite viewer)."""
from pathlib import Path
import streamlit as st
from PIL import Image

def render(row, fixes, idx, root: Path, width: int = 256):
    st.subheader("Satellite observation")
    img = root / row["image_path"]
    if img.exists():
        st.image(Image.open(img).resize((width, width)),
                 caption=f"{row['image_path']} · {row['channels']} · {row['satellite_source']}")
    else:
        st.warning(f"Missing frame: {row['image_path']}")
    # filmstrip: prev / current / next
    cols = st.columns(3)
    for j, label in ((idx - 1, "−6h"), (idx, "now"), (idx + 1, "+6h")):
        with cols[(j - idx) + 1]:
            if 0 <= j < len(fixes):
                p = root / fixes[j]["image_path"]
                if p.exists():
                    st.image(Image.open(p).resize((96, 96)), caption=label)
                else:
                    st.caption(f"{label} (missing)")
            else:
                st.caption(f"{label} (—)")
