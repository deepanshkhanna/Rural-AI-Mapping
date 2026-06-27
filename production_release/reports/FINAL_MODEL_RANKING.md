# FINAL MODEL RANKING

Generated from per-candidate certification runs (598 val patches, NADALA + NAGUL, TTA + calibrated pipeline).

## Ranking criteria (in order)

1. FG mIoU (calibrated + postprocess)
2. Road IoU
3. Water IoU
4. Calibration stability (bias magnitude)
5. Class balance (no single-class dominance artifact)

## Results table

| Rank | Candidate | FG mIoU | Road IoU | Water IoU | Built-Up IoU | Bridge IoU | Bias-search FG |
|------|-----------|---------|----------|-----------|--------------|------------|----------------|
| 1 | **epoch_71** | 0.4809 | 0.4356 | 0.7466 | 0.7415 | 0.0000 | 0.5091 |
| 2 | **epoch_33** | 0.4751 | 0.4256 | 0.7314 | 0.7434 | 0.0000 | 0.5069 |
| 3 | **epoch_69** | 0.4698 | 0.4397 | 0.6970 | 0.7426 | 0.0000 | 0.5102 |
| 4 | **epoch_80** | 0.4627 | 0.4339 | 0.6749 | 0.7421 | 0.0000 | 0.5079 |

## Winner

**epoch_71** — highest FG mIoU (0.4809) and highest Water IoU (0.7466) among viable candidates.

Ensemble configuration: `best_model.pth` (epoch 71, model_state_dict) + `latest_model.pth` (epoch 80, ema_state_dict), weights 0.65 / 0.35.

## Rollback candidate

**epoch_69** — highest Road IoU (0.4397) if road recall is prioritized over aggregate FG mIoU.

## Excluded

- ResNet18 legacy checkpoints (not in matrix)
- epoch_80 alone — lowest FG mIoU (0.4627)
