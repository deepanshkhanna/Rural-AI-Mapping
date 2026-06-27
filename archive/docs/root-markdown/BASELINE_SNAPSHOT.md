# BASELINE SNAPSHOT — Certified V1 (epoch_71)

**Frozen:** 2026-06-16  
**Tag:** `v1.0-certified`  
**Purpose:** Comparison target for all future experiments.

## Production Metrics (calibrated + TTA + postprocess)

| Metric | Value |
|--------|-------|
| **FG mIoU** | **0.4809** |
| Road IoU | 0.4356 |
| Water IoU | 0.7466 |
| Built-Up IoU | 0.7415 |
| Bridge IoU | 0.0000 |
| Confidence | 0.82 |

598 validation patches, NADALA + NAGUL.

## Checkpoint Hashes

| Artifact | SHA-256 |
|----------|---------|
| `production_release/checkpoints/best_model.pth` (epoch 71) | `8675e06ae0584bd5105b88f2e8356777d85d7eaeb585c4b4381a087162f7d892` |
| `production_release/checkpoints/latest_model.pth` (epoch 80 EMA) | `f8f45947be59825fbb6addc54c75d748f1722d57bb636299bfe9a1da51ca1aa7` |

## Calibration Hash

| Artifact | SHA-256 |
|----------|---------|
| `production_release/bias/optimal_bias.json` | `4ff3321bb6aa06c46e834f844ea0e3a1b574e806bd0515c4531b71e51d0e788e` |

Bias vector: `[-0.5, 0.75, 0.0, -0.5, -0.5]`

## Benchmark Hashes

| Artifact | SHA-256 |
|----------|---------|
| `production_release/metrics/epoch_71_results.json` | `14f53a12e3332ac15f81d663ff5a0a83b141093b5d6b0fab4928feae1c82d4c4` |
| `production_release/metrics/epoch_33_results.json` | `1ed83b7810619890011ede8427c397de283bcb15301d7fd2b0345a5919c4f3a5` |
| `production_release/metrics/epoch_69_results.json` | `f1af3f40bddf52191af2e2bddf86ff27d457b786d7538be3997249a26eb8f488` |
| `production_release/metrics/epoch_80_results.json` | `14b3728fb3f9af80f91a26360892bc3ad87d4414a31681cb8b976549294a9d25` |
| `production_release/MANIFEST.json` | `cf6eb3cb6da88119e2c37306034b1132d68df0d186cdc3a15dbf8219c2626cf5` |

## Ensemble Configuration

- best@71 weight 0.65 + latest@80 EMA weight 0.35
- Architecture: DeepLabV3Plus-ResNet50 (26,735,987 parameters)

## Replacement Criteria

An experimental result may replace this baseline only when all four gates pass (see `research/README.md`).
