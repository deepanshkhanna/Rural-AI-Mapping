# Inference Validation Report

Date: 2026-06-07
Scope: calibrated engine, evaluation pipeline, API inference path, checkpoint loading

## 1) Calibrated Engine

- Method: Import and symbol resolution check
- Evidence: `ENGINE_CLASS_OK CalibratedEngine`
- Result: PASS (module loadable)

## 2) Evaluation Pipeline

- Method: Execute `run_calibrated_eval.py`
- Command: `PYTHONPATH=. .venv/bin/python run_calibrated_eval.py --help` (script starts full flow)
- Evidence: startup banner appears, then fails on checkpoint lookup
- Error: `FileNotFoundError: Checkpoint not found: outputs/checkpoints/best_model.pth`
- Result: FAIL in current environment due missing runtime checkpoints

## 3) API Inference Path

- Method A: direct auth + path checks with startup bypass
  - `GET /health` without key -> 401
  - `GET /health` with key -> 200
- Method B: successful inference with dummy initialized engine and valid PNG
  - Evidence: `INFER_VALID_STATUS 200`
  - Response keys: `class_stats`, `height`, `inference_seconds`, `width`
- Result: PASS (route behavior verified)

## 4) Checkpoint Loading

- Method: direct function probe and test evidence
- Evidence:
  - Missing-file protection: `FileNotFoundError Checkpoint not found: ...`
  - Test suite includes strict secure-loader behavior (`tests/test_config_security_eval.py`) and passed.
- Result: PASS (restrictions enforced)

## Inference Validation Verdict

- PARTIAL PASS
- Inference code paths are functional and secure, but calibrated evaluation cannot run end-to-end without local checkpoint artifacts.
