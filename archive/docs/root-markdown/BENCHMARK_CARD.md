# BENCHMARK CARD — Certified Model (epoch_71)

## Headline metrics (calibrated + TTA + postprocess)

| Metric | Value |
|--------|-------|
| **FG mIoU** | **0.4809** |
| Road IoU | 0.4356 |
| Built-Up IoU | 0.7415 |
| Water IoU | 0.7466 |
| Bridge IoU | 0.0000 |

## Evaluation protocol

| Field | Value |
|-------|-------|
| Evaluator | `run_calibrated_eval.py` |
| Validation patches | **598** |
| Villages | NADALA + NAGUL (2 held-out orthomosaics) |
| Patch size | 768×768 |
| Ensemble | best@71 (0.65) + latest@80 EMA (0.35) |
| Bias | `[-0.5, 0.75, 0.0, -0.5, -0.5]` |
| TTA | Horizontal + vertical flip average |
| Postprocess | Road gap fill, mask cleanup, bridge recovery |

## Stress results (winner only)

| Test | FG mIoU |
|------|---------|
| TTA on | 0.4809 |
| TTA off | 0.4755 |

### Per-village (TTA)

| Village | FG mIoU | Road | Water | Built-Up |
|---------|---------|------|-------|----------|
| NADALA | 0.5882 | 0.4180 | 0.6183 | 0.7282 |
| NAGUL | 0.4124 | 0.3574 | 0.6334 | 0.6588 |

## Known limitations

1. Bridge class not detectable (IoU 0.0).
2. Large village-to-village variance (NADALA vs NAGUL).
3. Patch-level validation ≠ full orthomosaic raster score.
4. Train villages (6) disjoint from val villages (2).

## Evidence

`production_release/metrics/epoch_71_results.json`
