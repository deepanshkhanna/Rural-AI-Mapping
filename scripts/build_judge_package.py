#!/usr/bin/env python3
"""Build judge_package/ for offline demo fallback."""
from __future__ import annotations
import json, shutil, sys
from pathlib import Path
import geopandas as gpd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "judge_package"
OUT.mkdir(exist_ok=True)
GPKG = ROOT / "outputs" / "roof_test.gpkg"
PREVIEW = ROOT / "demo_dataset/previews/04_fattu_bhila_building_heavy.jpg"
TIFF = ROOT / "demo_dataset/tiffs/04_fattu_bhila_building_heavy.tif"
METRICS = ROOT / "production_release/metrics/epoch_71_results.json"

for p in list(OUT.glob("*")):
    if p.is_file(): p.unlink()

if PREVIEW.exists():
    shutil.copy(PREVIEW, OUT / "01_original_ortho_preview.jpg")
elif TIFF.exists():
    from PIL import Image
    import rasterio, numpy as np
    with rasterio.open(TIFF) as src:
        d = src.read([1,2,3], window=rasterio.windows.Window(0,0,min(2048,src.width),min(2048,src.height)))
    Image.fromarray(np.transpose(d,(1,2,0)).astype(np.uint8)).save(OUT / "01_original_ortho_preview.jpg")

if GPKG.exists():
    shutil.copy(GPKG, OUT / "04_demo_vectors.gpkg")
    b = gpd.read_file(GPKG, layer="building_footprints")
    if "roof_type_code" in b.columns:
        s = b[["area_m2","roof_type_code"]].head(20)
        s.to_csv(OUT / "05_roof_type_code_sample.csv", index=False)
        fig, ax = plt.subplots(figsize=(8,4)); ax.axis("off")
        ax.table(cellText=s.values, colLabels=s.columns, loc="center")
        ax.set_title("roof_type_code sample")
        fig.savefig(OUT / "05_roof_type_code_attribute_table.png", dpi=150, bbox_inches="tight")
        plt.close()

if METRICS.exists():
    shutil.copy(METRICS, OUT / "06_certified_metrics_epoch_71.json")
if (ROOT/"docs/ARCHITECTURE.md").exists():
    shutil.copy(ROOT/"docs/ARCHITECTURE.md", OUT / "07_architecture.md")
if (ROOT/"submission/SUBMISSION_AUDIT.md").exists():
    shutil.copy(ROOT/"submission/SUBMISSION_AUDIT.md", OUT / "08_submission_audit.md")

manifest = {"tile": "04_fattu_bhila_building_heavy", "files": sorted(p.name for p in OUT.iterdir())}
(OUT/"manifest.json").write_text(json.dumps(manifest, indent=2))
print(json.dumps(manifest, indent=2))
