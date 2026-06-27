# SVAMITVA — Certified Submission Package

Geospatial segmentation for village infrastructure (Road, Built-Up, Water) from drone orthomosaics.

## Certified model

**epoch_71 ensemble** — FG mIoU **0.4809** (patch validation, NADALA + NAGUL).

## Start here

1. `BENCHMARK_CARD.md` — verified metrics
2. `MODEL_CARD.md` — architecture and ensemble
3. `DATASET_CARD.md` — data splits and validation
4. `SVAMITVA_FINAL_PRODUCTION_DECISION.md` — selection rationale
5. `FINAL_MODEL_CERTIFICATION.md` — certification record
6. `production_release/` — frozen bias, metrics, manifest (checkpoints via [CHECKPOINT_RECOVERY.md](../CHECKPOINT_RECOVERY.md))

## Reproduce metrics

```bash
pip install -r requirements.txt
# Restore checkpoints from GitHub release v1.0-certified (recovery_bundle_v1.zip) — see CHECKPOINT_RECOVERY.md
cp production_release/checkpoints/*.pth outputs/checkpoints/
mkdir -p outputs && cp production_release/bias/optimal_bias.json outputs/optimal_bias.json
python run_calibrated_eval.py --require-bias
```

Requires production GeoTIFF data per `config/platform_config.v1.json` (not redistributed in this package).

## Limitations

- Bridge class not operational (IoU 0.0).
- Metrics on 598 validation patches, not full orthomosaic raster pass.
- See `BENCHMARK_CARD.md` for per-village stress results.
