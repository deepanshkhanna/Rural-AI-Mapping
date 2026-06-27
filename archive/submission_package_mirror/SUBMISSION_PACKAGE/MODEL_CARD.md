# MODEL CARD

## Model

| Field | Value |
|-------|-------|
| Name | SVAMITVA Production Ensemble |
| Architecture | DeepLabV3Plus |
| Encoder | ResNet50 (ImageNet init) |
| Parameters | 26,735,987 |
| Classes | 5 (BG, Road, Bridge, Built-Up, Water) |
| Certified candidate | **epoch_71** |
| Experiment | `recovery_run` |

## Ensemble

| Component | Checkpoint | Epoch | Weight | State key |
|-----------|------------|-------|--------|-----------|
| Best | `best_model.pth` | 71 | 0.65 | `model_state_dict` |
| Latest | `latest_model.pth` | 80 | 0.35 | `ema_state_dict` |

## Training summary

| Field | Value |
|-------|-------|
| Epochs completed | 80 |
| Best val checkpoint | Epoch 71 |
| Image size | 768 |
| Batch size | 4 |
| Loss | v2 (class-balanced) |
| Sampling | Class-balanced patches |
| Train villages | 6 GeoTIFF orthomosaics |
| Val villages | NADALA, NAGUL (held out) |

## Evaluation summary

| Metric | Calibrated |
|--------|------------|
| FG mIoU | 0.4809 |
| Road | 0.4356 |
| Built-Up | 0.7415 |
| Water | 0.7466 |
| Bridge | 0.0000 |

## Bias calibration

Per-class logit bias from coordinate-descent search on validation ensemble logits:

`[-0.5, 0.75, 0.0, -0.5, -0.5]` (BG, Road, Bridge, Built-Up, Water)

File: `production_release/bias/optimal_bias.json`

## Known weaknesses

- Bridge detection fails completely.
- Road IoU weaker on NAGUL (0.36) than aggregate (0.44).
- Postprocessing provides minimal FG delta (~0.0) for this checkpoint.

## Recommended use

- Village infrastructure mapping for **Road, Built-Up, Water** on SVAMITVA orthomosaics similar to training distribution.
- Sliding-window / tiled inference via `CalibratedEngine.predict_tiff`.

## Non-recommended use

- Bridge inventory or cadastral bridge claims.
- Single global metric without per-village disclosure.
- Citing archived 0.3871 FG mIoU from `docs/audit-archive/`.
