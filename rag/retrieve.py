"""TF-IDF cosine retrieval over rag/index.pkl — top-k chunks with citations."""
from __future__ import annotations
import pickle
import re
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "rag" / "index.pkl"
TOKEN = re.compile(r"[a-z0-9]+")

def _load():
    if not INDEX.exists():
        raise RuntimeError("rag/index.pkl missing — run python -m rag.ingest")
    with open(INDEX, "rb") as f:
        return pickle.load(f)

def query_vector(q: str, vocab: dict, idf: np.ndarray) -> np.ndarray:
    toks = TOKEN.findall(q.lower())
    n = len(toks) or 1
    v = np.zeros(len(vocab))
    counts: dict[str, int] = {}
    for t in toks:
        if t in vocab:
            counts[t] = counts.get(t, 0) + 1
    for t, k in counts.items():
        v[vocab[t]] = (k / n) * idf[vocab[t]]
    return v / (np.linalg.norm(v) or 1.0)

def retrieve(question: str, top_k: int = 5) -> list[dict]:
    index = _load()
    qv = query_vector(question, index["vocab"], index["idf"])
    scores = index["matrix"] @ qv
    order = np.argsort(-scores)[:top_k]
    out = []
    for r in order:
        c = index["chunks"][int(r)]
        out.append({**c, "score": float(scores[int(r)])})
    return out

def cite(chunk: dict) -> str:
    return f"{chunk.get('source', '?')} — {chunk.get('title', chunk['id'])} [{chunk['id']}]"
