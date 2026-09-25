"""Prediction service: PyTorch checkpoints preferred, numpy fallback.

Backend contract (TRD §7): numbers always come from ML checkpoints.
Torch presence is detected at load; absence never breaks the API.
"""
from __future__ import annotations
from functools import lru_cache
from pathlib import Path
import numpy as np
from api import config as C
from models.features import frame_features
from models.intensity import IntensityBundle
from models import track as T

class Predictors:
    backend: str = "numpy"

    def __init__(self):
        self.intensity = IntensityBundle.load(C.INTENSITY_CKPT)
        self.track = T.load_model(C.TRACK_CKPT)
        tm = self._try_torch()
        if tm:
            self.torch = tm
            self.backend = "torch"
        else:
            self.torch = None

    @staticmethod
    def _try_torch():
        if not (C.TORCH_INTENSITY_CKPT.exists() and C.TORCH_TRACK_CKPT.exists()):
            return None
        try:
            from models import torch_models as TM
            return TM.load_predictors(C.TORCH_INTENSITY_CKPT, C.TORCH_TRACK_CKPT)
        except Exception:
            return None

    def features(self, image_path: str, lat: float, lon: float, wind: float) -> np.ndarray:
        img = frame_features([str(Path(image_path))])
        meta = np.array([[lat, lon, wind]], dtype=np.float32)
        return np.hstack([img, meta])

    def classify(self, X: np.ndarray, image_paths: list[str] | None = None):
        if self.torch is not None:
            try:
                return self.torch.classify(X, image_paths)
            except Exception:
                pass
        return self.intensity.predict(X)

    def track_next(self, lat, lon, dlat_last, dlon_last, wind):
        if self.torch is not None:
            try:
                return self.torch.track_next(lat, lon, dlat_last, dlon_last, wind)
            except Exception:
                pass
        return T.predict_next(self.track, lat, lon, dlat_last, dlon_last, wind)

@lru_cache
def get_predictors() -> Predictors:
    return Predictors()
