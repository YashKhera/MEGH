"""RAG service: FastAPI -> Retriever -> (LLM | template).

Retriever: local TF-IDF index (FAISS + sentence-transformers upgrade path in
requirements-torch.txt). LLM: OpenAI-compatible chat endpoint configured via
MEGH_LLM_URL/KEY/MODEL; without it, deterministic template answers are used.
The LLM never produces numbers — prediction block passes through verbatim.
"""
from __future__ import annotations
import requests
from api import config as C
from rag.retrieve import retrieve, cite
from rag.rerank import rerank
from rag.prompts import build_prompt, template_answer

def gather(question: str, top_k: int = 6, final: int = 5) -> list[dict]:
    return rerank(question, retrieve(question, top_k=top_k))[:final]

def llm_answer(question: str, prediction: dict, chunks: list[dict]) -> str | None:
    if not (C.LLM_URL and C.LLM_KEY):
        return None
    try:
        r = requests.post(
            C.LLM_URL.rstrip("/") + "/chat/completions",
            headers={"Authorization": f"Bearer {C.LLM_KEY}"},
            json={"model": C.LLM_MODEL,
                  "messages": [{"role": "system",
                                 "content": "You explain cyclone predictions with citations. "
                                            "Never invent numbers."},
                                {"role": "user",
                                 "content": build_prompt(question, prediction, chunks)}],
                  "temperature": 0.2, "max_tokens": 400},
            timeout=30)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
    except Exception:
        return None

def explain(question: str, prediction: dict) -> dict:
    try:
        chunks = gather(question)
    except RuntimeError as e:
        return {"answer": f"RAG index missing ({e}). Run python -m rag.ingest.",
                "sources": [], "llm": False, "note": "index-missing"}
    text = llm_answer(question, prediction, chunks)
    used_llm = text is not None
    if not used_llm:
        text = template_answer(question, prediction, chunks)
    sources = [{"id": c["id"], "title": c.get("title", ""), "source": c.get("source", ""),
                "url": c.get("url", ""), "citation": cite(c),
                "score": round(c.get("rerank_score", 0.0), 3)} for c in chunks]
    return {"answer": text, "sources": sources, "llm": used_llm,
            "note": "llm-grounded" if used_llm else "retrieval + template (no LLM key)"}
