# Data Manifest

## Repository Policy

This repository is code-and-configuration only. Raw datasets, geospatial source files, and generated outputs are excluded from version control.

## Required Runtime Inputs (Local, Not Tracked)

- `outputs/checkpoints/best_model.pth`
- `outputs/checkpoints/latest_model.pth`
- `outputs/optimal_bias.json` (optional but recommended)
- Approved demo imagery (`.png`, `.jpg`, `.jpeg`, `.tif`, `.tiff`)

## Explicitly Excluded From Git

- `data/**`
- `outputs/**`
- `Test/**`
- `demo_ui/assets/samples/**`
- Geospatial binaries (`*.tif`, `*.tiff`, `*.shp`, `*.dbf`, `*.gpkg`, etc.)

## Acquisition Instructions

1. Pull approved source datasets from the official SVAMITVA secure storage channel.
2. Place raw data under local `data/` only.
3. Generate checkpoints and outputs locally into `outputs/`.
4. Verify `git status` is clean before commit to ensure no data artifacts are tracked.

## Compliance Check

Use:

```bash
rg --files | rg "(data/|outputs/|Test/|demo_ui/assets/samples/)"
```

Expected result: no tracked raw data artifacts, only policy files and optional `.gitkeep` placeholders.
