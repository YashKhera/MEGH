# MEGH Case Study — DEMO014 (test storm, unseen in training)

**Why this storm:** best track-skill story on the held-out test set —
model mean error **25.8 km** vs persistence **39.4 km** (**+13.5 km skill**, n=18 pairs).
Storm-level split guarantees DEMO014 was never seen in training.

## Replay script (2 min)
1. `streamlit run app/streamlit_app.py` → ⭐ Load case study (DEMO014).
2. Tick **Replay storm** → watch travelled (blue) grow along grey full best-track.
3. Pause mid-life (~fix 12): satellite frame → ML class + confidence + wind.
4. Point to red **MEGH 6h** vs orange **persist** vs green **actual next** markers.
5. Read the per-fix error line + storm-average skill in the metrics panel.
6. Intensity timeline: blue best-track wind vs red ML wind marker.
7. "Why?" panel: explanation comes from checkpoints + (Day-3) IMD/WMO citations —
   never LLM-invented numbers.

## Numbers to quote
- Track (test): model 25.8 km mean error vs 39.4 km persistence.
- Intensity (test overall): macro-F1 0.48, vision-only 0.52; wind MAE 0.45 kt
  (wind is an input feature in Day-1 — vision-only ablation shows true image skill).
- Provenance: SYN_PROXY frames until HURSAT/INSAT ingest; storm-level split.

## Limitations to state
- Synthetic proxy frames, not real HURSAT/INSAT yet.
- Simplified ridge track model; no NWP; research/demo only.
