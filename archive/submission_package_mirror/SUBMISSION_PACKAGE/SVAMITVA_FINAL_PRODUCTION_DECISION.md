# SVAMITVA FINAL PRODUCTION DECISION

## 1. Which checkpoint won?

**epoch_71** — ensemble of `best_model.pth` (epoch 71) + `latest_model.pth` (epoch 80).

## 2. Why did it win?

Highest **FG mIoU = 0.4809** among four measured candidates, with best **Water IoU = 0.7466**.

## 3. What evidence supports the decision?

| Candidate | FG mIoU | Road | Water |
|-----------|---------|------|-------|
| epoch_33 | 0.4751 | 0.4256 | 0.7314 |
| epoch_69 | 0.4698 | 0.4397 | 0.6970 |
| **epoch_71** | **0.4809** | 0.4356 | **0.7466** |
| epoch_80 | 0.4627 | 0.4339 | 0.6749 |

Artifacts: `outputs/certification/epoch_*_results.json`, stress on winner in `epoch_71_results.json`.

## 4. What calibration was used?

Per-candidate coordinate-descent bias search. Winner bias: `[-0.5, 0.75, 0.0, -0.5, -0.5]`

## 5. What metrics are defensible?

Calibrated + TTA + postprocess metrics on 598 deterministic validation patches over NADALA and NAGUL production GeoTIFFs. Per-village breakdown in stress report.

## 6. What limitations remain?

- Bridge class unusable (IoU 0.0)
- NAGUL underperforms NADALA
- Patch-val metrics ≠ full submission raster scores

## 7. Is the model submission-ready?

**Yes, with documented limitations.** Bridge claims are not defensible. FG/Road/Water/Built-Up claims are supported by measured eval.

## 8. Confidence level

**0.82** — complete sequential certification, no OOM, all candidates measured, release frozen.

---

## CERTIFIED PRODUCTION MODEL

```
PRODUCTION_MODEL = epoch_71 ensemble
CHECKPOINT_BEST  = outputs/checkpoints/best_model.pth
CHECKPOINT_LATEST = outputs/checkpoints/latest_model.pth
BIAS_FILE        = outputs/certification/bias/optimal_bias_epoch_71.json
FROZEN_RELEASE   = production_release/
```
