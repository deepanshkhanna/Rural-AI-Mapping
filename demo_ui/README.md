# Demo UI — AI Infrastructure Mapping System

Lightweight Streamlit interface for visualizing SVAMITVA segmentation outputs.

**This is a demo layer only — isolated from the core ML pipeline.**
Delete this directory entirely to remove it without affecting training or inference.

---

## Quick Start

```bash
# From project root
cd <project_root>
streamlit run demo_ui/app.py
```

Open **http://localhost:8501** in your browser.

---

## Features

| Feature | Details |
|---|---|
| File upload | PNG / JPG / JPEG / TIFF (drag & drop or browse) |
| Live preview | Shown immediately after upload |
| Inference | Sliding-window (512px patches, 64px overlap) |
| Results | Original · Mask · Overlay side-by-side |
| Overlay toggle | Blend mask over image at α=0.45 |
| Class stats | Per-class pixel % with color bars |
| Download | Export segmentation mask as PNG |
| Model info | Checkpoint paths, runtime device, and submission-scope warning |

---

## Architecture

```
demo_ui/
├── app.py               — Streamlit UI (dark theme, animations)
├── inference_wrapper.py — Model loading + sliding-window inference
├── assets/              — Static assets (if any)
└── README.md            — This file
```

`inference_wrapper.py` imports from:
- `src/models/model_factory.py` → `create_model()`
- `outputs/checkpoints/best_model.pth` and `outputs/checkpoints/latest_model.pth` → ensemble inference inputs

**No core files are modified.**

---

## Classes

| ID | Name | Color |
|---|---|---|
| 0 | Background | Black `#000000` |
| 1 | Road | Red `#ff0000` |
| 2 | Bridge | Blue `#0000ff` |
| 3 | Built-Up Area | Yellow `#ffff00` |
| 4 | Water Body | Cyan `#00c8ff` |

## Metric Provenance For Demo Claims

- Demo-facing performance claims must use only `official_metrics_for_submission.md`.
- Evaluator: `run_calibrated_eval.py`.
- Checkpoint pipeline: `outputs/checkpoints/best_model.pth` (EMA epoch 43) + `outputs/checkpoints/latest_model.pth` (EMA epoch 80).
- Calibration: enabled (`outputs/optimal_bias.json`).
- TTA: enabled.
- Postprocessing: enabled.
- Generated artifact/date: `outputs/calibrated_eval_results.json` (2026-06-07 00:37:33 +0530).

---

## Removal

```bash
rm -rf demo_ui/
```

Core training (`train.py`) and inference (`test_inference.py`) are unaffected.
