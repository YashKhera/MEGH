"""Image features for MVP: stateless stats from 64x64 proxy frames.

Keeps Day-1 trainable without torch. When torch/ResNet18 lands (requirements-torch.txt),
it should output the same interface: features(X) -> (n, d) + embedding_dim.
"""
from __future__ import annotations
import numpy as np
from PIL import Image

def frame_features(paths_or_arrays, size: int = 64) -> np.ndarray:
    feats = []
    for item in paths_or_arrays:
        if isinstance(item, (str, bytes)) or hasattr(item, "__fspath__"):
            img = Image.open(item).convert("L").resize((size, size))
            a = np.asarray(img, dtype=np.float32) / 255.0
        else:
            a = np.asarray(item, dtype=np.float32)
            if a.max() > 1.5:
                a = a / 255.0
        h, w = a.shape[-2:]
        cy, cx = h / 2, w / 2
        yy, xx = np.mgrid[0:h, 0:w]
        r = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / (w / 2)
        core = a[r < 0.35].mean() if (r < 0.35).any() else a.mean()
        ring = a[(r >= 0.35) & (r < 0.8)].mean()
        outer = a[r >= 0.8].mean() if (r >= 0.8).any() else a.mean()
        feats.append([a.mean(), a.std(), float(a.min()), float(a.max()),
                      float(core), float(ring), float(outer),
                      float(core - outer), float(core - ring)])
    return np.array(feats, dtype=np.float32)
