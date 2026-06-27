# HOSTILE REVIEWER REPORT

Simulated challenges to submission claims and defensible responses.

## Challenge: "Road IoU is only 0.44 — weak for cadastral roads."

**Response (defensible):** Certified Road IoU = **0.4356** on 598 held-out patches. NAGUL alone is **0.3574**; NADALA **0.4180**. Document village variance; do not claim uniform road quality.

**Do not claim:** State-wide road mapping accuracy or >0.55 Road IoU.

## Challenge: "Water IoU 0.75 seems high — overfitting?"

**Response (defensible):** Water IoU **0.7466** measured with frozen bias on held-out NADALA+NAGUL. Bias search FG on logits was 0.509; postprocess+TTA pipeline yields reported class IoUs. NAGUL Water **0.6334** shows generalization gap.

**Do not claim:** Water works equally on unseen regions without eval.

## Challenge: "Bridge is in the taxonomy but useless."

**Response (defensible):** Bridge IoU **0.0000** on 6,290 GT pixels. README and MODEL_CARD exclude Bridge from operational claims.

**Do not claim:** Bridge detection capability.

## Challenge: "598 patches is tiny."

**Response (defensible):** Acknowledged limitation. Patches are deterministic, minority-augmented, on 2 production villages. Metrics are patch-val, not leaderboard full-scene.

**Do not claim:** Statistically representative national validation.

## Challenge: "Bias tuning inflates scores."

**Response (defensible):** Per-candidate bias search documented. Winner bias `[-0.5, 0.75, 0.0, -0.5, -0.5]`. Repro eval with same bias reproduces FG **0.4809**. Postprocess delta ≈ 0.

**Do not claim:** Zero-calibration raw-model performance equals reported FG mIoU.

## Challenge: "Generalization to new villages unproven."

**Response (defensible):** Only NADALA + NAGUL measured. Train on 6 disjoint villages.

**Do not claim:** Zero-shot performance on arbitrary Indian villages without local validation.

## Summary

| Claim type | Defensible? |
|------------|-------------|
| FG mIoU 0.4809 (patch val, calibrated) | YES |
| Per-class IoU table | YES |
| epoch_71 selection vs 3 alternatives | YES |
| Bridge detection | NO |
| Archived 0.3871 metrics | NO |
| Full-raster leaderboard score | NO |
| Uniform cross-village performance | NO |
