"""Vision encoder — TRD §3.

Day-1: stateless proxy (see features.py). Torch ResNet18/EfficientNet-B0 upgrade
plugs in here later behind the same `embed()` function without changing callers.
"""
from .features import frame_features

def embed(paths_or_arrays):
    return frame_features(paths_or_arrays)
