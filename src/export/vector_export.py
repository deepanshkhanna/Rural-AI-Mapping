"""Export segmentation masks to GeoPackage with optional roof_type_code."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import geopandas as gpd
import numpy as np
import pandas as pd
from rasterio.features import shapes
from rasterio.transform import Affine
from shapely.geometry import shape
from shapely.validation import make_valid

from src.postprocessing import CLASS_BUILTUP, CLASS_ROAD, CLASS_WATER, classify_rooftops

try:
    from src.roof_material.classifier import RoofMaterialClassifier
    from src.roof_material.crops import extract_polygon_crop
    from src.roof_material.flags import ROOF_CLASSIFIER_ENABLED
except ImportError:
    RoofMaterialClassifier = None  # type: ignore[misc, assignment]
    extract_polygon_crop = None  # type: ignore[misc, assignment]
    ROOF_CLASSIFIER_ENABLED = False  # type: ignore[misc, assignment]

_LAYER_CONFIG = {
    "building_footprints": (CLASS_BUILTUP, 100, True),
    "roads": (CLASS_ROAD, 200, False),
    "water_bodies": (CLASS_WATER, 500, False),
}


def _as_affine(transform: Affine | list[float] | tuple[float, ...]) -> Affine:
    return transform if isinstance(transform, Affine) else Affine(*list(transform)[:6])


def _binary_mask_for_layer(mask: np.ndarray, class_id: int, *, use_rooftop_heuristic: bool) -> np.ndarray:
    if use_rooftop_heuristic and class_id == CLASS_BUILTUP:
        return classify_rooftops(mask).astype(np.uint8)
    return (mask == class_id).astype(np.uint8)


def _polygonize_binary_mask(binary, transform, *, min_area_px, simplify_tolerance_m, pixel_size_m):
    if binary.sum() == 0:
        return []
    feats = []
    min_area_m2 = float(min_area_px) * pixel_size_m ** 2
    tol = simplify_tolerance_m if simplify_tolerance_m is not None else pixel_size_m * 0.5
    for geom, value in shapes(binary, mask=binary.astype(bool), transform=transform):
        if int(value) != 1:
            continue
        poly = make_valid(shape(geom))
        if poly.is_empty or poly.area < min_area_m2:
            continue
        if tol > 0:
            poly = poly.simplify(tolerance=tol, preserve_topology=True)
        if poly.is_empty:
            continue
        feats.append({"geometry": poly, "area_m2": round(float(poly.area), 2),
                      "area_px": int(round(poly.area / pixel_size_m ** 2)),
                      "perimeter_m": round(float(poly.length), 2)})
    return feats


def annotate_buildings_with_roof_types(gdf, ortho_path, classifier, *, batch_size=64):
    if gdf.empty or extract_polygon_crop is None or not ROOF_CLASSIFIER_ENABLED:
        return gdf
    ortho_path = Path(ortho_path)
    if not ortho_path.exists():
        return gdf
    out = gdf.copy()
    crops, valid_idx = [], []
    for i, row in out.iterrows():
        crop = extract_polygon_crop(ortho_path, row.geometry)
        if crop is not None:
            crops.append(crop)
            valid_idx.append(i)
    codes: list[int | None] = [None] * len(out)
    for start in range(0, len(crops), batch_size):
        batch_codes = classifier.predict_codes(crops[start : start + batch_size])
        for offset, code in enumerate(batch_codes):
            codes[valid_idx[start + offset]] = code
    out["roof_type_code"] = pd.array(codes, dtype="Int64")
    return out


def layer_to_geodataframe(mask, layer_name, transform, crs, *, pixel_size_m=0.3, min_area_px=None,
                          simplify_tolerance_m=None, building_use_rooftop_heuristic=True,
                          ortho_path=None, roof_classifier=None):
    class_id, default_min_px, default_heuristic = _LAYER_CONFIG[layer_name]
    affine = _as_affine(transform)
    min_px = min_area_px if min_area_px is not None else default_min_px
    use_heuristic = building_use_rooftop_heuristic if layer_name == "building_footprints" else default_heuristic
    binary = _binary_mask_for_layer(mask, class_id, use_rooftop_heuristic=use_heuristic)
    feats = _polygonize_binary_mask(binary, affine, min_area_px=min_px,
                                    simplify_tolerance_m=simplify_tolerance_m, pixel_size_m=pixel_size_m)
    if not feats:
        return gpd.GeoDataFrame(columns=["layer", "area_m2", "area_px", "perimeter_m", "geometry"],
                                geometry="geometry", crs=crs)
    gdf = gpd.GeoDataFrame(feats, geometry="geometry", crs=crs)
    gdf.insert(0, "layer", layer_name)
    gdf.insert(1, "class_id", class_id)
    if layer_name == "building_footprints" and ortho_path and roof_classifier and ROOF_CLASSIFIER_ENABLED:
        gdf = annotate_buildings_with_roof_types(gdf, ortho_path, roof_classifier)
    return gdf


def export_mask_vectors(mask, transform, crs, output_path, *, pixel_size_m=0.3,
                        layers=("building_footprints", "roads", "water_bodies"),
                        building_use_rooftop_heuristic=True, simplify_tolerance_m=None,
                        min_areas_px=None, ortho_path=None, roof_classifier=None):
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        out.unlink()
    min_areas_px = min_areas_px or {}
    counts = {}
    for i, layer_name in enumerate(layers):
        gdf = layer_to_geodataframe(mask, layer_name, transform, crs, pixel_size_m=pixel_size_m,
                                    min_area_px=min_areas_px.get(layer_name),
                                    simplify_tolerance_m=simplify_tolerance_m,
                                    building_use_rooftop_heuristic=building_use_rooftop_heuristic,
                                    ortho_path=ortho_path if layer_name == "building_footprints" else None,
                                    roof_classifier=roof_classifier if layer_name == "building_footprints" else None)
        counts[layer_name] = len(gdf)
        gdf.to_file(out, layer=layer_name, driver="GPKG", mode="w" if i == 0 else "a", engine="pyogrio")
    return counts


def mask_to_geopackage(mask, meta, output_path, **kwargs):
    transform = meta.get("transform")
    if transform is None:
        raise ValueError("meta must include transform")
    return export_mask_vectors(mask, transform, meta.get("crs", "EPSG:3857"), output_path,
                               pixel_size_m=float(meta.get("pixel_size_m", 0.3)), **kwargs)


def export_vectors_zip(mask, meta, zip_path, *, gpkg_name="svamitva_vectors.gpkg", **kwargs):
    import tempfile, zipfile
    zip_path = Path(zip_path)
    with tempfile.TemporaryDirectory() as tmp:
        gpkg = Path(tmp) / gpkg_name
        counts = mask_to_geopackage(mask, meta, gpkg, **kwargs)
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.write(gpkg, arcname=gpkg_name)
    return {"layers": counts, "zip_path": str(zip_path), "gpkg_name": gpkg_name}
