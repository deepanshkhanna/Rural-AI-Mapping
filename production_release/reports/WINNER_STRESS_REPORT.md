# WINNER STRESS REPORT — epoch_71

## Full validation (TTA + calibrated + postprocess)

| Metric | Value |
|--------|-------|
| FG mIoU | 0.4809 |
| Road IoU | 0.4356 |
| Built-Up IoU | 0.7415 |
| Water IoU | 0.7466 |
| Bridge IoU | 0.0000 |

## TTA vs no-TTA

| Mode | FG mIoU |
|------|---------|
| TTA enabled | 0.4809 |
| TTA disabled | 0.4755 |

TTA uplift: +0.0054

## Per-village (TTA)

| Village | FG mIoU | Road | Water | Built-Up |
|---------|---------|------|-------|----------|
| NADALA | 0.5882 | 0.4180 | 0.6183 | 0.7282 |
| NAGUL | 0.4124 | 0.3574 | 0.6334 | 0.6588 |

## Observations

- NADALA FG mIoU materially higher than NAGUL (larger orthomosaic, different class mix).
- NAGUL is the harder village; road IoU drops to 0.36 on NAGUL alone.
- Bridge remains at 0.0000 under all stress modes.
- TTA provides modest but positive FG mIoU uplift.
