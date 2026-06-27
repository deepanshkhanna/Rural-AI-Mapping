"""Crop extraction and shapefile resolution for roof material training."""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
from rasterio import windows
from shapely.geometry import box

ROOT = Path(__file__).resolve().parents[2]

# Official integer codes in Built_Up shapefiles (not class indices).
ROOF_TYPE_CODES: tuple[int, ...] = (1, 2, 3, 4)
CODE_TO_INDEX: dict[int, int] = {code: i for i, code in enumerate(ROOF_TYPE_CODES)}
INDEX_TO_CODE: dict[int, int] = {i: code for code, i in CODE_TO_INDEX.items()}

VILLAGE_TILES: dict[str, dict[str, str]] = {
    "SAMLUR": {
        "split": "train",
        "region": "CG",
        "tiff": "data/Raz/Training_dataSet_3/SAMLUR_450163_SIYANAR_450164_KUTULNAR_450165_BINJAM_450166_JHODIYAWADAM_450167_ORTHO.tif",
    },
    "MURDANDA": {
        "split": "train",
        "region": "CG",
        "tiff": "data/Raz/Training_dataSet_2/MURDANDA_450879_AWAPALLI_CHINTAKONTA_ORTHO.tif",
    },
    "BADETUMNAR": {
        "split": "train",
        "region": "CG",
        "tiff": "data/Raz/Training_dataSet_2/BADETUMNAR_450157_BANGAPAL_450155_CHHOTETUMAR_450149_MOFALNAR_450150_ORTHO.tif",
    },
    "KUTRU": {
        "split": "train",
        "region": "CG",
        "tiff": "data/Raz/Training_dataSet_2/KUTRU_451189_AAKLANKA_451163_ORTHO.tif",
    },
    "PINDORI": {
        "split": "train",
        "region": "PB",
        "tiff": "data/Raz/PB_training_dataSet_shp_file/PINDORI MAYA SINGH-TUGALWAL_28456_ortho.tif",
    },
    "TIMMOWAL": {
        "split": "train",
        "region": "PB",
        "tiff": "data/Raz/PB_training_dataSet_shp_file/TIMMOWAL_37695_ORI.tif",
    },
    "NADALA": {
        "split": "val",
        "region": "PB",
        "tiff": "data/Raz/PB_training_dataSet_shp_file/28996_NADALA_ORTHO.tif",
    },
    "NAGUL": {
        "split": "val",
        "region": "CG",
        "tiff": "data/Raz/Training_dataSet_3/NAGUL_450171_MADASE_450172_GHOTPAL_450137_ORTHO.tif",
    },
}


def resolve_built_up_shapefile(region: str) -> Path:
    """Return readable Built-Up shapefile path (handles broken symlinks)."""
    if region == "PB":
        candidates = [
            ROOT / "data/Raz/PB_training_dataSet_shp_file/shp-file/Built_Up_Area_typ.shp",
            ROOT
            / "archive/downloads/extracted/PB_training_dataSet_shp_file/PB_training_dataSet_shp_file/Punjab_shp_file/Built_Up_Area_typ.shp",
        ]
    else:
        candidates = [
            ROOT / "data/Raz/CG_shp-file/shp-file/Built_Up_Area_type.shp",
            ROOT / "archive/downloads/extracted/CG_shp-file/CG_shp-file/Built_Up_Area_type.shp",
        ]
    for path in candidates:
        if path.exists():
            return path
    raise FileNotFoundError(f"No Built-Up shapefile found for region={region!r}")


def load_built_up_for_village(village: str) -> tuple[gpd.GeoDataFrame, Path]:
    """Load building polygons intersecting a village ortho extent."""
    if village not in VILLAGE_TILES:
        raise KeyError(f"Unknown village {village!r}")
    meta = VILLAGE_TILES[village]
    tiff = ROOT / meta["tiff"]
    if not tiff.exists():
        raise FileNotFoundError(f"Orthomosaic missing: {tiff}")

    shp_path = resolve_built_up_shapefile(meta["region"])
    gdf = gpd.read_file(shp_path)

    with rasterio.open(tiff) as src:
        bounds = src.bounds
        crs = src.crs

    gdf = gdf.to_crs(crs)
    bbox = box(bounds.left, bounds.bottom, bounds.right, bounds.top)
    sub = gdf[gdf.intersects(bbox)].copy()
    sub = sub[sub["Roof_type"].isin(ROOF_TYPE_CODES)]
    return sub, tiff


def extract_polygon_crop(
    ortho_path: str | Path,
    geometry,
    *,
    size: int = 224,
    pad_ratio: float = 0.10,
    min_side_px: int = 32,
    bands: tuple[int, ...] = (1, 2, 3),
) -> np.ndarray | None:
    """
    Extract an RGB chip for a polygon geometry in ortho pixel space.

    Returns (3, size, size) float32 in [0, 1], or None if too small / invalid.
    """
    ortho_path = Path(ortho_path)
    with rasterio.open(ortho_path) as src:
        gdf = gpd.GeoDataFrame(geometry=[geometry], crs=src.crs)
        bounds = gdf.total_bounds
        minx, miny, maxx, maxy = bounds
        width_m = maxx - minx
        height_m = maxy - miny
        if width_m <= 0 or height_m <= 0:
            return None

        pad_x = width_m * pad_ratio
        pad_y = height_m * pad_ratio
        win = windows.from_bounds(
            minx - pad_x,
            miny - pad_y,
            maxx + pad_x,
            maxy + pad_y,
            transform=src.transform,
        )
        win = win.intersection(windows.Window(0, 0, src.width, src.height))
        if win.width < min_side_px or win.height < min_side_px:
            return None

        data = src.read(indexes=list(bands), window=win, boundless=True, fill_value=0)
        if data.shape[1] < min_side_px or data.shape[2] < min_side_px:
            return None

        # Resize to target using cv2 (lazy import keeps module light).
        import cv2

        img = np.transpose(data, (1, 2, 0)).astype(np.float32) / 255.0
        resized = cv2.resize(img, (size, size), interpolation=cv2.INTER_LINEAR)
        return np.transpose(resized, (2, 0, 1))
