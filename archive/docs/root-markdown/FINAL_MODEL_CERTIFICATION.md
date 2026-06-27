# FINAL MODEL CERTIFICATION

## CERTIFIED SUBMISSION MODEL

| Field | Value |
|-------|-------|
| **Designation** | `PRODUCTION_MODEL` / `CERTIFIED_SUBMISSION_MODEL` |
| **Winner candidate** | epoch_71 |
| **Best checkpoint** | `outputs/checkpoints/best_model.pth` (epoch 71) |
| **Latest checkpoint** | `outputs/checkpoints/latest_model.pth` (epoch 80) |
| **Ensemble weights** | 0.65 best + 0.35 latest EMA |
| **Calibration file** | `outputs/certification/bias/optimal_bias_epoch_71.json` |
| **Optimal bias** | `[-0.5, 0.75, 0.0, -0.5, -0.5]` |

## Certified metrics (calibrated eval, 598 patches, TTA)

| Metric | Value |
|--------|-------|
| FG mIoU | **0.4809** |
| Road IoU | 0.4356 |
| Built-Up IoU | 0.7415 |
| Water IoU | 0.7466 |
| Bridge IoU | 0.0000 |

## Rationale

Selected by measured FG mIoU ranking across four recoverable ResNet50 ensemble candidates. epoch_71 wins on FG mIoU and Water IoU while maintaining competitive Road and Built-Up performance.

## Known limitations

1. **Bridge IoU = 0.0000** — bridge class not usable for submission claims.
2. **Village variance** — NAGUL FG mIoU (0.41) substantially below NADALA (0.59).
3. **Road** — epoch_69 scores higher on Road alone; epoch_71 trades ~0.4 pp Road for +5 pp Water vs epoch_69.
4. Metrics are patch-validation on NADALA+NAGUL only; not full-raster submission scores.

## Rollback candidate

`epoch_69` ensemble (timed checkpoint ep69 + latest ep80) — Road IoU 0.4397.

## Confidence score

**0.82 / 1.00** — All four candidates evaluated with identical protocol, per-candidate bias search, and persisted JSON artifacts. Bridge failure and village imbalance prevent higher confidence.

## Frozen release

Immutable copy at `production_release/` — see `PRODUCTION_RELEASE_MANIFEST.md`.
