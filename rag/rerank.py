"""Lightweight rerank: blend TF-IDF score with question-term coverage.

Kept intentionally simple per 06_72_HOUR_PLAN.md cut order (reranker is optional).
"""
from __future__ import annotations
import re

TOKEN = re.compile(r"[a-z0-9]+")
STOP = {"the", "a", "an", "is", "was", "why", "what", "how", "does", "do", "of",
        "for", "in", "on", "to", "this", "that", "it", "as", "with", "and", "or"}

def rerank(question: str, chunks: list[dict], weight: float = 0.35) -> list[dict]:
    qt = {t for t in TOKEN.findall(question.lower()) if t not in STOP}
    out = []
    for c in chunks:
        ct = set(TOKEN.findall(c["text"].lower()))
        cover = len(qt & ct) / (len(qt) or 1)
        out.append({**c, "rerank_score": c.get("score", 0.0) + weight * cover})
    return sorted(out, key=lambda c: -c["rerank_score"])
