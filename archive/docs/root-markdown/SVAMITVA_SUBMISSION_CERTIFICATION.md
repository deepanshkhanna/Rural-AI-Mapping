# SVAMITVA SUBMISSION CERTIFICATION

**Certified:** 2026-06-16

## 1. What is the certified model?

**epoch_71 ensemble:** DeepLabV3Plus-ResNet50, 26,735,987 parameters.

- `best_model.pth` epoch 71 (weight 0.65)
- `latest_model.pth` epoch 80 EMA (weight 0.35)
- Bias: `[-0.5, 0.75, 0.0, -0.5, -0.5]`

Frozen at `production_release/`.

## 2. What metrics are verified?

| Metric | Value | Verified by |
|--------|-------|-------------|
| FG mIoU | **0.4809** | `run_calibrated_eval.py` reproduction |
| Road IoU | 0.4356 | Repro eval |
| Built-Up IoU | 0.7415 | Repro eval |
| Water IoU | 0.7466 | Repro eval |
| Bridge IoU | 0.0000 | Repro eval |

598 patches, NADALA + NAGUL, calibrated + TTA + postprocess.

## 3. What claims are supported?

- FG / Road / Built-Up / Water IoU on held-out patch validation (table above).
- epoch_71 selection over epochs 33, 69, 80 with identical protocol.
- Per-village stress: NADALA FG 0.5882, NAGUL FG 0.4124.
- Exact reproducibility from `production_release/`.

## 4. What claims are unsupported?

- Bridge detection.
- Archived FG mIoU 0.3871 or `docs/SYSTEM_OVERVIEW.md` legacy metrics.
- Full-raster or leaderboard placement.
- Uniform performance across all Indian villages.

## 5. Can reviewers reproduce results?

**Yes.** See `REPRODUCIBILITY_AUDIT.md`. Deploy frozen release artifacts and run:

```bash
python run_calibrated_eval.py --require-bias
```

## 6. Is the submission ready?

**YES** — with documented limitations. Package at `SUBMISSION_PACKAGE/`.

## 7. Final confidence score

**0.84 / 1.00**

Production certification (0.82) plus independent reproducibility verification (+0.02). Bridge failure and small validation set cap confidence.

---

**Status: CERTIFIED SUBMISSION**
