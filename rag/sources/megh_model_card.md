# MEGH model card (condensed for retrieval)
Title: MEGH model card
Source: Team Vittvanni (MEGH project)
URL: local:docs/09_MODEL_CARD.md
Date: 2026-09-25
Topic: methodology
Basin: North Indian Ocean

Purpose: historical analysis and research demonstration of cyclone identification,
intensity classification, wind estimation, and 6-hour movement prediction.
Users: researchers, students, analysts, demonstrators. Not for public alerts,
dispatch, aviation/maritime decisions, or replacing official warnings.

Method: image statistics + position/wind features feed a softmax intensity
classifier and ridge wind regressor; a ridge delta model predicts 6h displacement
against a persistence baseline (repeat last displacement). Evaluation is
storm-level held out: test storms are never seen in training. Metrics: macro-F1,
balanced accuracy, wind MAE/RMSE, mean great-circle track error in km.

Limitations: synthetic proxy frames (not real HURSAT/INSAT yet), basin-specific
behaviour, class imbalance, historical label uncertainty, small MVP data,
simplified track model, no numerical weather prediction, no operational skill
guarantee. Confidence is not safety.
