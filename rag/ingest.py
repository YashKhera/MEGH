"""RAG ingest — chunk rag/sources/*.md, build TF-IDF index (04_RAG_STRATEGY.md).

Stdlib + numpy only (sentence-transformers needs torch: see requirements-torch.txt).
Chunk metadata per 04_RAG_STRATEGY.md: source, title, URL, date, topic, basin.

Usage: python -m rag.ingest [--rebuild]
Writes: rag/index.pkl  (chunks + vocab + idf + tfidf matrix)
"""
from __future__ import annotations
import argparse
import pickle
import re
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "rag" / "sources"
INDEX = ROOT / "rag" / "index.pkl"

META_KEYS = ("Title", "Source", "URL", "Date", "Topic", "Basin")
TOKEN = re.compile(r"[a-z0-9]+")

def tokenize(text: str) -> list[str]:
    return TOKEN.findall(text.lower())

def parse_source(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8")
    meta: dict = {"file": path.name}
    body_lines = []
    for line in text.splitlines():
        m = re.match(r"^(Title|Source|URL|Date|Topic|Basin):\s*(.*)$", line)
        if m:
            meta[m.group(1).lower()] = m.group(2).strip()
        else:
            body_lines.append(line)
    return meta, "\n".join(body_lines).strip()

def chunk_text(body: str, size: int = 900, overlap: int = 150) -> list[str]:
    paras = [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip()]
    chunks, cur = [], ""
    for p in paras:
        if len(cur) + len(p) + 2 <= size:
            cur = (cur + "\n\n" + p).strip()
        else:
            if cur:
                chunks.append(cur)
            if len(p) > size:  # hard-split long paragraph
                for i in range(0, len(p), size - overlap):
                    chunks.append(p[i:i + size])
                cur = ""
            else:
                cur = p
    if cur:
        chunks.append(cur)
    return chunks or [body]

def build_index() -> dict:
    docs = sorted(SOURCES.glob("*.md"))
    if not docs:
        raise SystemExit(f"no sources in {SOURCES}")
    chunks: list[dict] = []
    for d in docs:
        meta, body = parse_source(d)
        for i, ch in enumerate(chunk_text(body)):
            chunks.append({"id": f"{d.stem}#{i}", **meta, "text": ch})
    # vocab + df
    df: dict[str, int] = {}
    tok_chunks = []
    for c in chunks:
        toks = sorted(set(tokenize(c["text"] + " " + c.get("title", "") + " " + c.get("topic", ""))))
        tok_chunks.append(toks)
        for t in toks:
            df[t] = df.get(t, 0) + 1
    vocab = {t: i for i, t in enumerate(sorted(df))}
    N = len(chunks)
    idf = np.array([np.log((1 + N) / (1 + df[t])) + 1.0 for t in sorted(df)], dtype=np.float64)
    mat = np.zeros((N, len(vocab)), dtype=np.float64)
    for r, c in enumerate(chunks):
        toks = tokenize(c["text"])
        n = len(toks) or 1
        counts: dict[str, int] = {}
        for t in toks:
            if t in vocab:
                counts[t] = counts.get(t, 0) + 1
        for t, k in counts.items():
            mat[r, vocab[t]] = (k / n) * idf[vocab[t]]
        norm = np.linalg.norm(mat[r]) or 1.0
        mat[r] /= norm
    index = {"chunks": chunks, "vocab": vocab, "idf": idf, "matrix": mat}
    INDEX.parent.mkdir(parents=True, exist_ok=True)
    with open(INDEX, "wb") as f:
        pickle.dump(index, f)
    print(f"[ingest] {len(docs)} sources -> {len(chunks)} chunks, vocab={len(vocab)} -> {INDEX}")
    return index

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rebuild", action="store_true")
    a = ap.parse_args()
    if INDEX.exists() and not a.rebuild:
        print(f"[ingest] {INDEX} exists (use --rebuild to refresh)")
        return
    build_index()

if __name__ == "__main__":
    main()
