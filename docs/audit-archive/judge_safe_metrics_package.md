# Judge-Safe Metrics Package

Single source of truth for board-facing performance claims.

| Metric | Official Value | Evaluator | Checkpoint Pipeline | Calibration | Date / Artifact |
|---|---:|---|---|---|---|
| Foreground mIoU | 0.3871 | `run_calibrated_eval.py` | `best_model.pth` EMA epoch 43 + `latest_model.pth` EMA epoch 80 | Enabled (`outputs/optimal_bias.json`) | 2026-06-07 00:37:33 +0530 / `outputs/calibrated_eval_results.json` |
| Road IoU | 0.5555 | Same | Same | Enabled | Same |
| Road Precision | 0.7141 | Same | Same | Enabled | Same |
| Road Recall | 0.7144 | Same | Same | Enabled | Same |
| Road F1 | 0.7142 | Same | Same | Enabled | Same |
| Bridge IoU | 0.0000 | Same | Same | Enabled | Same |
| Bridge Precision | 0.0000 | Same | Same | Enabled | Same |
| Bridge Recall | 0.0000 | Same | Same | Enabled | Same |
| Bridge F1 | 0.0000 | Same | Same | Enabled | Same |
| Built-Up IoU | 0.1615 | Same | Same | Enabled | Same |
| Built-Up Precision | 0.1750 | Same | Same | Enabled | Same |
| Built-Up Recall | 0.6767 | Same | Same | Enabled | Same |
| Built-Up F1 | 0.2780 | Same | Same | Enabled | Same |
| Water Body IoU | 0.8315 | Same | Same | Enabled | Same |
| Water Body Precision | 0.9962 | Same | Same | Enabled | Same |
| Water Body Recall | 0.8342 | Same | Same | Enabled | Same |
| Water Body F1 | 0.9080 | Same | Same | Enabled | Same |

Bridge claim policy: bridge is non-operational in current submission scope and excluded from success claims.

Use policy: do not cite any metric outside this table in judging communication.