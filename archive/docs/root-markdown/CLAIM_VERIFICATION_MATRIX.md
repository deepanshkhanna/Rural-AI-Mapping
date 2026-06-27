# CLAIM VERIFICATION MATRIX

| Claim | Status | Evidence artifact | Notes |
|-------|--------|-------------------|-------|
| FG mIoU = 0.4809 (certified) | **SUPPORTED** | `production_release/metrics/epoch_71_results.json` | run_calibrated_eval.py reproduced 0.4809 |
| Road IoU = 0.4356 | **SUPPORTED** | `epoch_71_results.json → summary.road_iou` | Repro eval Road 0.4356 |
| Water IoU = 0.7466 | **SUPPORTED** | `epoch_71_results.json` | Repro eval Water 0.7466 |
| Built-Up IoU = 0.7415 | **SUPPORTED** | `epoch_71_results.json` | Repro eval BU 0.7415 |
| Bridge IoU = 0.0 | **SUPPORTED** | `epoch_71_results.json` | Do not claim bridge detection |
| epoch_71 selected over 4 candidates | **SUPPORTED** | `FINAL_MODEL_RANKING.md + 4 result JSONs` | Sequential certification |
| NADALA FG mIoU 0.5882 | **SUPPORTED** | `epoch_71_results.json per_village_tta` | Stress eval only |
| NAGUL FG mIoU 0.4124 | **SUPPORTED** | `epoch_71_results.json per_village_tta` | Stress eval only |
| 598 validation patches | **SUPPORTED** | `epoch_71_results.json val_patches` | UnifiedMultiClassDataset val split |
| FG mIoU 0.3871 (SYSTEM_OVERVIEW) | **STALE/UNSUPPORTED** | `docs/SYSTEM_OVERVIEW.md L17` | Superseded archived model; do not cite |
| Road IoU 0.5555 (SYSTEM_OVERVIEW) | **STALE/UNSUPPORTED** | `docs/SYSTEM_OVERVIEW.md L18` | Archived metrics only |
| EMA epoch 43 checkpoint | **STALE/UNSUPPORTED** | `docs/SYSTEM_OVERVIEW.md L26` | Current model is epoch 71/80 |
| Bridge operational class | **UNSUPPORTED** | `FINAL_MODEL_CERTIFICATION.md` | Bridge excluded from claims |
| Full-raster submission IoU | **UNSUPPORTED** | `—` | Only patch-val measured; not full ortho raster pass |
| Leaderboard rank / placement | **UNSUPPORTED** | `—` | No external leaderboard run in certification |
| make judge produces production metrics | **PARTIAL** | `README.md` | Synthetic CI path; production needs real data + release artifacts |

## Rule

Only cite metrics from `production_release/metrics/epoch_71_results.json` or freshly run `run_calibrated_eval.py` with frozen release artifacts.
