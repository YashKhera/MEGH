"""Evidence & explanation panel — Day-2 template, Day-3 RAG grounding."""
import streamlit as st

def render(question_key="megh_why"):
    st.subheader("Why? — evidence & explanation")
    q = st.text_input("Ask about this prediction",
                      "Why was this observation classified as its intensity class?",
                      key=question_key)
    if st.button("Explain", key=question_key + "_go"):
        st.info("Day-2 template: numbers above come from ML checkpoints "
                "(intensity.pkl, track.pkl). Day-3 RAG will attach IMD/WMO/IBTrACS "
                f"citations here. Question saved: {q[:200]}")
    st.caption("RAG = explanation only. It never overwrites ML numbers (TRD boundary).")
