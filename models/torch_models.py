"""PyTorch models for MEGH (TRD §3): transfer-learning vision + track MLP.

Vision: timm backbone (resnet18 default) -> embedding + meta MLP -> heads for
  (a) intensity classification, (b) wind regression.
Track: MLP on (dlat_last, dlon_last, speed, hsin, hcos, lat, lon, wind) -> (dlat, dlon).

Checkpoints: models/checkpoints/torch_intensity.pt / torch_track.pt.
The API prefers these when present and falls back to numpy .pkl otherwise.
CPU-trainable at MVP scale (844 frames).
"""
from __future__ import annotations
from pathlib import Path
import numpy as np

try:
    import torch
    import torch.nn as nn
    import timm
    _TORCH = True
except ImportError:
    _TORCH = False

from models import track as T

IMG_SIZE = 64
TRACK_FEATS = T.FEATS


def build_backbone(name: str = "resnet18"):
    if not _TORCH:
        raise RuntimeError("torch/timm not installed")
    m = timm.create_model(name, pretrained=True, num_classes=0, in_chans=1)
    dim = m.num_features
    for p in list(m.parameters())[:-10]:  # freeze early layers for 72h budget
        p.requires_grad = False
    return m, dim


class TorchIntensity(nn.Module):
    def __init__(self, n_classes: int, backbone: str = "resnet18"):
        super().__init__()
        self.cnn, dim = build_backbone(backbone)
        self.meta_mlp = nn.Sequential(nn.Linear(3, 16), nn.ReLU())
        self.head_cls = nn.Linear(dim + 16, n_classes)
        self.head_wind = nn.Linear(dim + 16, 1)

    def forward(self, img, meta):
        z = torch.cat([self.cnn(img), self.meta_mlp(meta)], dim=1)
        return self.head_cls(z), self.head_wind(z).squeeze(1)


class TorchTrack(nn.Module):
    def __init__(self, d_in: int = 8):
        super().__init__()
        self.net = nn.Sequential(nn.Linear(d_in, 32), nn.ReLU(),
                                 nn.Linear(32, 32), nn.ReLU(),
                                 nn.Linear(32, 2))

    def forward(self, x):
        return self.net(x)


class TorchBundle:
    """API-facing wrapper with the same semantics as the numpy predictors."""

    def __init__(self, intensity: TorchIntensity, track: TorchTrack,
                 classes: list[str], img_mean: float = 0.5, img_std: float = 0.25):
        self.intensity = intensity.eval()
        self.track = track.eval()
        self.classes = classes
        self.img_mean = img_mean
        self.img_std = img_std
        self._tmean = None
        self._tsd = None

    def set_track_norm(self, mu, sd):
        self._tmean = np.asarray(mu, float)
        self._tsd = np.asarray(sd, float)

    @staticmethod
    def _img_tensor(paths) -> "torch.Tensor":
        from PIL import Image
        arrs = []
        for p in paths:
            a = np.asarray(Image.open(p).convert("L").resize((IMG_SIZE, IMG_SIZE)),
                           dtype=np.float32) / 255.0
            arrs.append(a[None, :, :])
        t = torch.from_numpy(np.stack(arrs))
        return t

    @torch.no_grad()
    def classify(self, X_stats: np.ndarray, img_paths: list[str] | None = None):
        X_stats = np.asarray(X_stats, float)
        meta = torch.from_numpy(X_stats[:, -3:].astype(np.float32))
        if img_paths is not None:
            img = self._img_tensor(img_paths)
        else:  # stats-only fallback: neutral grey frame
            img = torch.full((len(X_stats), 1, IMG_SIZE, IMG_SIZE), 0.5)
        logits, wind = self.intensity(img, meta)
        prob = torch.softmax(logits, dim=1).numpy()
        idx = prob.argmax(axis=1)
        return [self.classes[i] for i in idx], prob.max(axis=1), wind.numpy()

    @torch.no_grad()
    def track_next(self, lat, lon, dlat_last, dlon_last, wind):
        speed = float(np.hypot(dlat_last, dlon_last))
        h = float(np.arctan2(dlon_last, dlat_last))
        x = np.array([[dlat_last, dlon_last, speed, np.sin(h), np.cos(h),
                       lat, lon, wind]], float)
        if self._tmean is not None:
            x = (x - self._tmean) / self._tsd
        d = self.track(torch.from_numpy(x.astype(np.float32))).numpy()[0]
        return float(lat + d[0]), float(lon + d[1]), float(d[0]), float(d[1])


def save_predictors(bundle: TorchBundle, track_model, ipath: Path, tpath: Path,
                    track_norm) -> None:
    ipath.parent.mkdir(parents=True, exist_ok=True)
    torch.save({"state": bundle.intensity.state_dict(),
                "classes": bundle.classes,
                "backbone": "resnet18"}, ipath)
    torch.save({"state": track_model.state_dict(), "norm": track_norm}, tpath)


def load_predictors(ipath: Path, tpath: Path) -> TorchBundle:
    from training.imd import CLASSES  # noqa
    di = torch.load(ipath, map_location="cpu", weights_only=False)
    dt = torch.load(tpath, map_location="cpu", weights_only=False)
    classes = di.get("classes") or CLASSES
    net = TorchIntensity(len(classes), di.get("backbone", "resnet18"))
    net.load_state_dict(di["state"])
    tr = TorchTrack()
    tr.load_state_dict(dt["state"])
    b = TorchBundle(net, tr, classes)
    if dt.get("norm"):
        b.set_track_norm(*dt["norm"])
    return b
