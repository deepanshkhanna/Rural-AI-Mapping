# Storage Reduction Report

**Date:** 2026-06-27

## Size Summary

| Metric | Value |
|--------|-------|
| **Before** | 106,274,199,420 bytes (~99.0 GB) |
| **After** | 104,816,094,531 bytes (~97.6 GB) |
| **Space reclaimed** | **~1.46 GB** (1,458,104,889 bytes) |

*Note: `data/` (69 GB) is gitignored local training data — not deleted.*

## Largest Directories (after)

| Path | Size | Purpose | Action |
|------|------|---------|--------|
| `data/` | 69 GB | Raw orthomosaics / roof crops | **KEEP** (training data) |
| `archive/` | ~16 GB | Experiments, mirrors, artifacts | **KEEP** (audit trail) |
| `production_release/` | 2.0 GB | Certified checkpoints + metrics | **KEEP** (protected) |
| `outputs/checkpoints/` | 714 MB | Runtime checkpoint copies for eval/demo | **KEEP** (required) |
| `demo_dataset/` | ~704 MB | Demo GeoTIFF tiles | **KEEP** (demo) |

## Deleted (evidence: zero production dependency)

| Path | Size (approx) | Reason |
|------|---------------|--------|
| `outputs/e2e_validation/` | 261 MB | Experimental CLI validation; no active imports |
| `outputs/roof_audit/` | 79 MB | Roof experiment artifacts |
| `outputs/roof_experiment/` | 4.8 MB | Failed/smoke experiment outputs |
| `outputs/*.log` | <1 MB | Debug logs |
| `outputs/layer_test*.gpkg`, `roof_test.gpkg` | ~2 MB | Test artifacts |
| `.pytest_cache/`, `.coverage` | ~1 MB | Regenerable |
| `archive/outputs-artifacts/tensorboard/` | minimal | Empty/stale TB dir |
| `archive/logs/*` | 108 KB | Stale training logs |

## Preserved (protected)

- `production_release/checkpoints/best_model.pth` (306 MB) — epoch 71
- `production_release/checkpoints/latest_model.pth` (408 MB) — epoch 80 EMA
- `production_release/metrics/epoch_71_results.json`
- `outputs/calibrated_eval_results.json`, `outputs/optimal_bias.json`
- `evidence/judge_package/`

## Rollback

All deletes logged in `submission/ROLLBACK_MANIFEST_2026-06-27.txt`.

**Restored during pass:** `src/export/vector_export.py` from git commit `54f6dee` (was missing; required for GIS export).
