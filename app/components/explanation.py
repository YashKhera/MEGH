"""Evidence & explanation panel — retrieval-grounded (Day-3).

Tries local RAG (retrieve+rerank+template) directly; falls back to FastAPI
/explain when backend=api. Never invents numbers: prediction block is passed
through verbatim and cited chunks are shown with source metadata.
"""
import streamlit as st

def render(question_key="megh_why", prediction=None, use_api=False):
    st.subheader("Why? — evidence & explanation")
    q = st.text_input("Ask about this prediction",
                      "Why was this observation classified as its intensity class?",
                      key=question_key)
    if st.button("Explain", key=question_key + "_go"):
        with st.spinner("Retrieving meteorological evidence…"):
            try:
                if use_api:
                    import requests
                    data = requests.post("http://127.0.0.1:8000/explain",
                                         json={"question": q,
                                               "prediction": prediction or {}},
                                         timeout=15).json()
                else:
                    from rag.retrieve import retrieve, cite
                    from rag.rerank import rerank
                    from rag.prompts import template_answer
                    chunks = rerank(q, retrieve(q, top_k=6))[:5]
                    data = {"answer": template_answer(q, prediction or {}, chunks),
                            "sources": [{"id": c["id"], "title": c.get("title", ""),
                                         "source": c.get("source", ""),
                                         "url": c.get("url", ""), "citation": cite(c),
                                         "score": round(c.get("rerank_score", 0.0), 3)}
                                        for c in chunks],
                            "note": "local TF-IDF RAG"}
            except Exception as e:
                data = {"answer": f"Retrieval unavailable ({e}). Run python -m rag.ingest.",
                        "sources": [], "note": "error"}
        st.write(data["answer"])
        if data.get("sources"):
            st.markdown("**Sources:**")
            for s in data["sources"]:
                st.markdown(f"- {s['citation']} — {s.get('url', '')}")
        st.caption(data.get("note", ""))
    st.caption("RAG = explanation only. It never overwrites ML numbers (TRD boundary).")
