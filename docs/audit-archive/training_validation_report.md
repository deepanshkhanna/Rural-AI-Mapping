# Training Validation Report

Date: 2026-06-07
Scope: Verify `train.py` executability and startup stages (dry-run)

## Verification Steps and Evidence

1. Entry-point sanity
- Command: `PYTHONPATH=. .venv/bin/python train.py --help`
- Result: PASS
- Evidence: CLI help rendered with full argument set.

2. Configuration load
- Command: `PYTHONPATH=. .venv/bin/python train.py --dry-run-loader --dry-run-batches 1 --num-epochs 1 --batch-size 2 --image-size 128`
- Result: PASS (config load), then runtime blocked at dataset stage
- Evidence: Training banner printed full config including device, classes, architecture, and hyperparameters.

3. Dataset resolution
- Command: same as above
- Result: FAIL
- Evidence: `ValueError: No valid TIFFs found across all sources` with missing SHP/TIFF warnings under `data/`.

4. Model build
- Command: direct model factory construction via platform config training keys.
- Result: PASS
- Evidence: `MODEL_BUILD_OK DeepLabV3Plus`

## Training Validation Verdict

- PARTIAL PASS
- `train.py` is executable, configuration loads, and model construction works.
- End-to-end dry-run loader cannot proceed in current repository state due intentionally removed local training datasets.
