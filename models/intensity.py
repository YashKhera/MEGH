"""Intensity classifier + wind regressor — numpy only (TRD §3-4).

Softmax regression (batch GD, class-balanced) on image stats + lat/lon/wind;
ridge closed-form for wind. Pickle checkpoint. Deterministic (seeded).
sklearn upgrade can plug in later behind same fit/predict/save/load API.
"""
from __future__ import annotations
import pickle
from pathlib import Path
import numpy as np

class Standardizer:
    def fit(self, X):
        self.mu = X.mean(axis=0)
        self.sd = X.std(axis=0) + 1e-8
        return self
    def transform(self, X):
        return (X - self.mu) / self.sd
    def fit_transform(self, X):
        return self.fit(X).transform(X)

def _softmax(Z):
    Z = Z - Z.max(axis=1, keepdims=True)
    E = np.exp(Z)
    return E / E.sum(axis=1, keepdims=True)

class IntensityBundle:
    def __init__(self):
        self.scaler = Standardizer()
        self.W = None
        self.b = None
        self.classes_: list[str] = []
        self.reg_w = None  # ridge weights incl bias
        self.reg_mu = None
        self.reg_sd = None

    def fit(self, X, y_class, y_wind, iters=600, lr=0.5, l2=1e-3):
        self.classes_ = sorted(set(y_class))
        ci = {c: i for i, c in enumerate(self.classes_)}
        Xs = self.scaler.fit_transform(np.asarray(X, float))
        n, d = Xs.shape
        K = len(self.classes_)
        Y = np.zeros((n, K))
        for i, c in enumerate(y_class):
            Y[i, ci[c]] = 1.0
        # class-balanced sample weights
        _, counts = np.unique(y_class, return_counts=True)
        wmap = {c: n / (len(counts) * counts[j]) for j, c in enumerate(sorted(set(y_class)))}
        sw = np.array([wmap[c] for c in y_class])[:, None]
        rng = np.random.default_rng(7)
        W = rng.normal(0, 0.01, (d, K))
        b = np.zeros(K)
        for _ in range(iters):
            P = _softmax(Xs @ W + b)
            G = (P - Y) * sw / n
            gradW = Xs.T @ G + l2 * W
            gradb = G.sum(axis=0)
            W -= lr * gradW
            b -= lr * gradb
        self.W, self.b = W, b
        # ridge for wind (closed form, standardized)
        mu, sd = Xs.mean(axis=0), Xs.std(axis=0) + 1e-8
        Xn = (Xs - mu) / sd
        A = np.hstack([Xn, np.ones((n, 1))])
        yw = np.asarray(y_wind, float)
        self.reg_w = np.linalg.solve(A.T @ A + 1.0 * np.eye(A.shape[1]), A.T @ yw)
        self.reg_mu, self.reg_sd = mu, sd
        return self

    def predict(self, X):
        Xs = self.scaler.transform(np.asarray(X, float))
        P = _softmax(Xs @ self.W + self.b)
        idx = P.argmax(axis=1)
        Xn = (Xs - self.reg_mu) / self.reg_sd
        A = np.hstack([Xn, np.ones((len(Xn), 1))])
        return [self.classes_[i] for i in idx], P.max(axis=1), A @ self.reg_w

    def save(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump({"W": self.W, "b": self.b, "classes": self.classes_,
                         "mu": self.scaler.mu, "sd": self.scaler.sd,
                         "reg_w": self.reg_w, "reg_mu": self.reg_mu,
                         "reg_sd": self.reg_sd}, f)

    @classmethod
    def load(cls, path: Path) -> "IntensityBundle":
        with open(path, "rb") as f:
            d = pickle.load(f)
        b = cls()
        b.W, b.b, b.classes_ = d["W"], d["b"], d["classes"]
        b.scaler.mu, b.scaler.sd = d["mu"], d["sd"]
        b.reg_w, b.reg_mu, b.reg_sd = d["reg_w"], d["reg_mu"], d["reg_sd"]
        return b
