# Demo Validation Report

Date: 2026-06-07
Scope: Streamlit startup, upload flow, prediction flow, visualization flow

## 1) Demo Startup

- Command: `PYTHONPATH=. .venv/bin/streamlit run demo_ui/app.py --server.headless true --server.port 8765`
- Result: PASS
- Evidence: server started and published local/network URLs.

## 2) Upload Flow

- Method: code-path review and shared platform limits in `demo_ui/app.py`
- Checks present: extension filtering and max upload size validation
- Result: PASS (validation logic present)

## 3) Prediction Flow

- Method: direct invocation of `demo_ui/inference_wrapper.predict_image`
- Evidence: `FileNotFoundError Checkpoint not found: ... outputs/checkpoints/best_model.pth`
- Result: FAIL in current environment (required checkpoints absent)

## 4) Visualization Flow

- Method: code-path review of overlay/statistics helpers in `demo_ui/app.py` + `demo_ui/inference_wrapper.py`
- Result: CONDITIONAL PASS
- Condition: requires successful model inference output, which is currently blocked by missing checkpoints.

## Demo Validation Verdict

- PARTIAL PASS
- UI service starts, but full upload->predict->visualize demonstration is not executable without local checkpoint artifacts.
