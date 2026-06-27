# RECOVERY BUNDLE REPORT

**Date:** 2026-06-16  
**Bundle:** `recovery_bundle_v1.zip`

## Contents

| Component | Description |
|-----------|-------------|
| `production_release/` | Frozen checkpoints, bias, metrics, reports, manifest |
| `submission_package/` | Self-contained reproducible evaluation package |
| `BENCHMARK_CARD.md` | Certified benchmark metrics |
| `MODEL_CARD.md` | Model architecture and ensemble details |
| `DATASET_CARD.md` | Dataset splits and validation protocol |
| `SVAMITVA_SUBMISSION_CERTIFICATION.md` | Official certification |
| `FINAL_MODEL_CERTIFICATION.md` | Production certification report |
| `PRODUCTION_RELEASE_MANIFEST.md` | Release manifest |
| `REPRODUCIBILITY_GUIDE.md` | Copy of `REPRODUCIBILITY_AUDIT.md` |
| `manifest.json` | Top-level copy of `production_release/MANIFEST.json` |

## Archive

| Property | Value |
|----------|------|
| File | `recovery_bundle_v1.zip` |
| Size | ~1.38 GB |
| Format | ZIP (deflate) |
| Location | Repository root (gitignored; attach to GitHub release) |

## Recovery Instructions

1. Extract `recovery_bundle_v1.zip` to a clean directory.
2. Copy `production_release/checkpoints/*.pth` → `outputs/checkpoints/`
3. Copy `production_release/bias/optimal_bias.json` → `outputs/optimal_bias.json`
4. Install dependencies: `pip install -r requirements.txt`
5. Ensure validation GeoTIFFs + shapefiles under `data/` per `config/platform_config.v1.json`
6. Run: `python run_calibrated_eval.py --require-bias`

Expected FG mIoU: **0.4809**

## Alternative: Submission Package

The `submission_package/` inside the bundle is fully self-contained for reviewer reproduction when paired with the geospatial dataset.

## Integrity

Verify checksums via `production_release/checksums/SHA256SUMS.txt` after extraction.
