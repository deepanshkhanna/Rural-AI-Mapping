# Training Dry-Run Report

## Loader dry-run (`train.py --dry-run-loader`)

- Exit code: **0**
- Batches observed: 2
- Bridge patch frequency: 0.75

## Model build + single batch

- Model: DeepLabV3Plus + resnet50 on `cuda`
- Optimizer: AdamW — **built**
- Forward/backward on batch [2, 3, 768, 768] → loss=1.5781
- Checkpoint dir writable: **True** (`outputs/checkpoints/`)

## Status

**PASS** — ready for production training launch.
