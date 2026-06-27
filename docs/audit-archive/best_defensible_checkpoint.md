# Best Defensible Checkpoint

## Decision

The best defensible submission checkpoint pipeline is:
- `outputs/checkpoints/best_model.pth` (EMA epoch 43)
- `outputs/checkpoints/latest_model.pth` (EMA epoch 80)

This is the exact checkpoint pair used by the official calibrated submission evaluator.

## Why This Is Defensible

- It is the same artifact path used for official scoring claims.
- It has explicit provenance in `official_metrics_for_submission.md`.
- It avoids cross-branch ambiguity from legacy and experimental runs.

## Provenance

- Evaluator: `run_calibrated_eval.py`
- Calibration: enabled (`outputs/optimal_bias.json`)
- TTA: enabled
- Postprocessing: enabled
- Date/source artifact: `outputs/calibrated_eval_results.json` (2026-06-07 00:37:33 +0530)

## Policy

- Do not use alternate checkpoint claims in board-facing communication.
- All score claims must be traceable to the official calibrated artifact chain.
