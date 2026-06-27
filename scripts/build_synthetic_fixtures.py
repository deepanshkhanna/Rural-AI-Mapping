#!/usr/bin/env python3
"""
Build synthetic geospatial fixtures and dummy checkpoints for CI/reproduce.

Creates:
  tests/fixtures/synthetic/ — GeoTIFF + shapefiles (EPSG:32643)
  outputs/checkpoints/best_model.pth, latest_model.pth
  outputs/optimal_bias.json

Usage:
    python scripts/build_synthetic_fixtures.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
import torch
from rasterio.transform import from_origin
from shapely.geometry import LineString, Polygon

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.config.platform_config import load_platform_config
from src.models.model_factory import create_model

FIXTURE_ROOT = ROOT / "tests" / "fixtures" / "synthetic"
TIFF_NAME = "SYNTHETIC_TEST_ORTHO.tif"
CRS = "EPSG:32643"
ORIGIN_X, ORIGIN_Y = 500000.0, 3200000.0
GSD = 0.5  # metres per pixel
SIZE = 1024


def _write_tiff(path: Path) -> None:
    """Synthetic ortho with RGB hints aligned to vector labels (verification benchmark)."""
    transform = from_origin(ORIGIN_X, ORIGIN_Y, GSD, GSD)
    rgb = np.full((3, SIZE, SIZE), 40, dtype=np.uint8)
    # Road corridor (y≈500): strong red signature
    rgb[0, 495:505, 200:800] = 255
    rgb[1, 495:505, 200:800] = 60
    # Built-up block: yellow signature
    rgb[0, 400:600, 400:600] = 230
    rgb[1, 400:600, 400:600] = 230
    rgb[2, 400:600, 400:600] = 40
    # Water body: blue signature
    rgb[0, 700:900, 100:300] = 30
    rgb[1, 700:900, 100:300] = 120
    rgb[2, 700:900, 100:300] = 255
    path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=SIZE,
        width=SIZE,
        count=3,
        dtype="uint8",
        crs=CRS,
        transform=transform,
    ) as dst:
        dst.write(rgb)


def _write_shapefiles(shp_dir: Path, tiff_bounds) -> None:
    shp_dir.mkdir(parents=True, exist_ok=True)
    minx, miny, maxx, maxy = tiff_bounds

    specs = {
        "Road.shp": (
            1,
            [LineString([(minx + 100 * GSD, miny + 500 * GSD), (minx + 800 * GSD, miny + 500 * GSD)])],
        ),
        "Bridge.shp": (
            2,
            [LineString([(minx + 400 * GSD, miny + 480 * GSD), (minx + 600 * GSD, miny + 520 * GSD)])],
        ),
        "Built_Up_Area_typ.shp": (
            3,
            [
                Polygon(
                    [
                        (minx + 400 * GSD, miny + 400 * GSD),
                        (minx + 600 * GSD, miny + 400 * GSD),
                        (minx + 600 * GSD, miny + 600 * GSD),
                        (minx + 400 * GSD, miny + 600 * GSD),
                    ]
                )
            ],
        ),
        "Water_Body.shp": (
            4,
            [
                Polygon(
                    [
                        (minx + 100 * GSD, miny + 700 * GSD),
                        (minx + 300 * GSD, miny + 700 * GSD),
                        (minx + 300 * GSD, miny + 900 * GSD),
                        (minx + 100 * GSD, miny + 900 * GSD),
                    ]
                )
            ],
        ),
    }

    for name, (class_id, geoms) in specs.items():
        gdf = gpd.GeoDataFrame({"class_id": [class_id] * len(geoms)}, geometry=geoms, crs=CRS)
        gdf.to_file(shp_dir / name)


def _write_checkpoints(out_dir: Path, image_size: int = 768) -> None:
    cfg = load_platform_config()
    config = {
        "architecture": str(cfg.training.get("architecture", "DeepLabV3Plus")),
        "encoder_name": str(cfg.training.get("encoder_name", "resnet50")),
        "encoder_weights": None,
        "classes": cfg.num_classes,
        "image_size": image_size,
        "patches_per_image": 4,
    }
    model = create_model(
        architecture=config["architecture"],
        encoder_name=config["encoder_name"],
        encoder_weights=None,
        in_channels=3,
        classes=config["classes"],
    )
    state = model.state_dict()
    out_dir.mkdir(parents=True, exist_ok=True)

    best = {
        "epoch": 1,
        "best_iou": 0.1,
        "config": config,
        "model_state_dict": state,
        "ema_state_dict": state,
    }
    latest = {
        "epoch": 2,
        "best_iou": 0.1,
        "config": config,
        "model_state_dict": state,
        "ema_state_dict": state,
    }
    torch.save(best, out_dir / "best_model.pth")
    torch.save(latest, out_dir / "latest_model.pth")


def _write_bias(out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "optimal_bias": [0.0, 0.0, 0.0, 0.0, 0.0],
        "source": "synthetic_zero_bias",
        "note": "Production bias [0,1.5,4,0,0] is invalid on synthetic checkpoints; use zeros.",
    }
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_dataset_layout() -> None:
    """Mirror DEFAULT_SOURCES layout under tests/fixtures/synthetic for validator."""
    tiff_dir = FIXTURE_ROOT / "tiffs"
    shp_dir = FIXTURE_ROOT / "shp"
    tiff_path = tiff_dir / TIFF_NAME
    _write_tiff(tiff_path)
    with rasterio.open(tiff_path) as src:
        bounds = src.bounds
    _write_shapefiles(shp_dir, bounds)

    manifest = {
        "synthetic": True,
        "tiff": str(tiff_path.relative_to(ROOT)),
        "shp_dir": str(shp_dir.relative_to(ROOT)),
        "crs": CRS,
        "gsd_m": GSD,
    }
    (FIXTURE_ROOT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-checkpoints", action="store_true", help="Only build geodata fixtures")
    args = parser.parse_args()

    _write_dataset_layout()
    if not args.skip_checkpoints:
        _write_checkpoints(ROOT / "outputs" / "checkpoints")
    _write_bias(ROOT / "outputs" / "optimal_bias.json")
    print(f"Wrote synthetic fixtures under {FIXTURE_ROOT}")
    if not args.skip_checkpoints:
        print("Wrote checkpoints under outputs/checkpoints/")
    print("Wrote outputs/optimal_bias.json (synthetic zero bias)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
