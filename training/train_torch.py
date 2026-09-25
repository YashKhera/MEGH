"""Train PyTorch intensity CNN + track MLP on MEGH dataset (pandas-free).

Usage:
    .\\.venv\\Scripts\\python.exe -m training.train_torch --epochs 5
Saves: models/checkpoints/torch_intensity.pt + torch_track.pt
The API auto-prefers these over numpy .pkl when present.
"""
from __future__ import annotations
import argparse
import csv
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]

def load_rows():
    with open(ROOT / "data" / "metadata" / "dataset.csv", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def main():
    import torch
    import torch.nn as nn
    from torch.utils.data import Dataset, DataLoader
    from PIL import Image
    from models.torch_models import TorchIntensity, TorchTrack, save_predictors
    from models import track as T

    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=5)
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--backbone", default="resnet18")
    a = ap.parse_args()

    rows = load_rows()
    classes = sorted({r["derived_class"] for r in rows})
    ci = {c: i for i, c in enumerate(classes)}

    class FrameDS(Dataset):
        def __init__(self, rr):
            self.rr = rr
        def __len__(self):
            return len(self.rr)
        def __getitem__(self, i):
            r = self.rr[i]
            img = np.asarray(Image.open(ROOT / r["image_path"]).convert("L").resize((64, 64)),
                             dtype=np.float32) / 255.0
            meta = np.array([float(r["latitude"]), float(r["longitude"]),
                             float(r["wind_kts"])], dtype=np.float32)
            return (torch.from_numpy(img[None]), torch.from_numpy(meta),
                    ci[r["derived_class"]], float(r["wind_kts"]))

    tr = [r for r in rows if r["split"] == "train"]
    loader = DataLoader(FrameDS(tr), batch_size=a.batch, shuffle=True)
    net = TorchIntensity(len(classes), a.backbone)
    opt = torch.optim.AdamW(filter(lambda p: p.requires_grad, net.parameters()), lr=3e-4)
    ce, huber = nn.CrossEntropyLoss(), nn.HuberLoss()
    net.train()
    for ep in range(a.epochs):
        tot, n = 0.0, 0
        for img, meta, yc, yw in loader:
            opt.zero_grad()
            logits, wind = net(img, meta)
            loss = ce(logits, yc) + 0.02 * huber(wind, yw)
            loss.backward()
            opt.step()
            tot += loss.item() * len(yc)
            n += len(yc)
        print(f"[torch] epoch {ep + 1}/{a.epochs} loss={tot / n:.4f}")

    # track MLP on standardized feats
    pairs = T.build_track_rows(rows)
    ptr = [r for r in pairs if r["split"] == "train"]
    X = np.array([[r[f] for f in T.FEATS] for r in ptr], float)
    Y = np.array([[r["dlat_next"], r["dlon_next"]] for r in ptr], float)
    mu, sd = X.mean(0), X.std(0) + 1e-8
    Xt = torch.from_numpy(((X - mu) / sd).astype(np.float32))
    Yt = torch.from_numpy(Y.astype(np.float32))
    tm = TorchTrack()
    opt2 = torch.optim.AdamW(tm.parameters(), lr=1e-3)
    tm.train()
    for ep in range(200):
        opt2.zero_grad()
        loss = nn.HuberLoss()(tm(Xt), Yt)
        loss.backward()
        opt2.step()
    print(f"[torch] track loss={loss.item():.5f}")

    bundle = type("B", (), {"intensity": net, "classes": classes})()
    save_predictors(bundle, tm, ROOT / "models" / "checkpoints" / "torch_intensity.pt",
                    ROOT / "models" / "checkpoints" / "torch_track.pt", (mu, sd))
    print("[torch] saved torch_intensity.pt + torch_track.pt")

if __name__ == "__main__":
    main()
