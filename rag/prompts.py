"""Grounded explanation prompts — LLM must not invent numbers (TRD boundary)."""
SYSTEM = ("You explain MEGH tropical-cyclone predictions using ONLY the retrieved "
          "evidence below plus the model prediction provided. Cite sources by id. "
          "Never invent wind speeds, positions, or metrics — copy them from the "
          "prediction block. If evidence is insufficient, say so.")

def build_prompt(question: str, prediction: dict, chunks: list[dict]) -> str:
    ev = "\n\n".join(f"[{c['id']}] ({c.get('source', '?')}): {c['text'][:700]}" for c in chunks)
    return (f"{SYSTEM}\n\nPREDICTION (from ML checkpoints, authoritative):\n{prediction}\n\n"
            f"EVIDENCE:\n{ev}\n\nQUESTION: {question}\n\n"
            "Answer in 4-6 sentences, then a 'Sources:' line listing chunk ids used.")

def _clean(text: str, limit: int = 300) -> str:
    """First content sentence, markdown headers stripped."""
    lines = [ln.strip().lstrip("# ").strip() for ln in text.split("\n")]
    lines = [ln for ln in lines if ln]
    if not lines:
        return ""
    first = lines[0]
    for sep in (". ", "; "):
        if sep in first:
            first = first.split(sep)[0] + "."
            break
    return first[:limit]

def template_answer(question: str, prediction: dict, chunks: list[dict]) -> str:
    """Deterministic offline answer (no LLM key needed): prediction + evidence."""
    lines = []
    if prediction:
        lines.append(
            f"MEGH's ML models (not the language model) produced: class "
            f"{prediction.get('class', prediction.get('intensity_class', '?'))} at "
            f"confidence {float(prediction.get('confidence', 0)):.0%}, wind "
            f"{float(prediction.get('wind_kts', 0)):.0f} kt.")
        nxt = prediction.get("next_6h") or {}
        if nxt:
            lines.append(f"6h movement: {nxt.get('lat')}, {nxt.get('lon')} "
                         f"(uncertainty {prediction.get('uncertainty_km', '?')} km).")
    for c in chunks[:3]:
        snippet = _clean(c["text"])
        if snippet:
            lines.append(f"Evidence ({c.get('source', '?')}): {snippet}")
    lines.append("Full cited sources are listed below; retrieval explains, it never "
                 "overwrites ML numbers.")
    return " ".join(lines)
