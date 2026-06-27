# Pipeline Recovery Report

**Timestamp (UTC):** 2026-06-15T14:45:45.236111+00:00

## UnifiedMultiClassDataset

- Train split: **PASS** — 12 patches, 6 TIFFs, sample image=(768, 768, 3), mask=(768, 768)
- Val split: **PASS** — 598 patches, 2 TIFFs, sample image=(768, 768, 3), mask=(768, 768)

## DatasetValidator

- Status: **PASS** (0 issues, 8 TIFFs, 12 shapefiles)

## Capabilities verified

- [x] Load train split (6 TIFFs per config)
- [x] Load val split (2 TIFFs: NADALA, NAGUL)
- [x] Generate patches (768px)
- [x] Rasterize labels
