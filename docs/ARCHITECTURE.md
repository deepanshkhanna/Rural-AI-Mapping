# Architecture

## Scope and Boundaries

- Operational classes: Road (1), Built-Up Area (3), Water Body (4)
- Non-operational class in current cycle: Bridge (2)
- Runtime config source: `config/platform_config.v1.json`

## Module Boundaries

- `src/config`: immutable platform config loader
- `src/datasets`: dataset reading, split control, and transforms
- `src/models`: model factory and architecture selection
- `src/training`: training loop and validation primitives
- `src/inference`: calibrated inference engine and export/eval helpers
- `src/evaluation`: unified metric computation utilities
- `src/security`: secure checkpoint loading
- `production`: API entrypoint and deployment runtime interface
- `demo_ui`: visualization-only frontend (not production dependency)

## Inference Path

```
Input image
  -> normalization
  -> calibrated ensemble inference (best + latest EMA checkpoints)
  -> optional TTA
  -> postprocessing pipeline
  -> class mask + class statistics
```

Production API uses `src/inference/calibrated_engine.py` directly and does not import UI modules.

## Security Controls

- Authenticated endpoints via API key header
- Startup validation for required environment and checkpoint artifacts
- Strict upload extension + MIME + size + dimension validation
- Checkpoint loading enforces `weights_only=True` without unsafe fallback

## Data Governance Controls

- Raw geospatial data directories and generated outputs are VCS-blocked in `.gitignore`
- Repository ships code/config only; data acquisition is documented in `data_manifest.md`

## Operational Metrics

Board-facing metrics and claims are sourced from `official_metrics_for_submission.md` only.
