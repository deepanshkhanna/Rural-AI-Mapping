# DATASET CARD

## Data sources

SVAMITVA production drone orthomosaics (GeoTIFF) + polygon shapefile labels (Road, Bridge, Built-Up, Water).

| Split | Villages | Stems |
|-------|----------|-------|
| **Train** | 6 | PINDORI MAYA SINGH-TUGALWAL, TIMMOWAL, BADETUMNAR cluster, MURDANDA, KUTRU, SAMLUR cluster |
| **Val** | 2 | `28996_NADALA_ORTHO`, `NAGUL_450171_MADASE_450172_GHOTPAL_450137_ORTHO` |

Config: `config/platform_config.v1.json`

## Patch construction

| Field | Value |
|-------|-------|
| Patch size | 768×768 px |
| Val patches total | **598** |
| Patches per image (val) | 50 (from checkpoint config) |
| Minority oversampling | 98 force-added patches for Road/Bridge/Water coverage |
| CRS | EPSG:3857 (reprojected as needed) |

## Validation methodology

- Deterministic patch grid on val TIFFs only.
- Labels rasterized from shapefiles per patch window.
- Metrics: pixel-level IoU, precision, recall, F1 via `compute_counts_metrics`.
- FG mIoU = mean IoU of present foreground classes (Road, Built-Up, Water; Bridge typically absent from mean when IoU=0).

## Limitations

1. **Small val set** — 2 villages, 598 patches; not a national sample.
2. **Geographic bias** — Punjab/Haryana production villages only.
3. **Bridge rarity** — 6,290 bridge GT pixels across val; model achieves 0 IoU.
4. **Patch vs raster** — Metrics on patches, not full-scene raster IoU.
5. **No held-out test third village** in certification bundle.

## Evidence

`outputs/certification/epoch_71_results.json` → `val_tiffs`, `val_patches`
