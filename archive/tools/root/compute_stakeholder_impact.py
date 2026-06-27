"""Compute stakeholder impact metrics for each validation village.

Uses validation TIFF bounds + source vector layers to estimate class coverage,
infrastructure density, and land-use indicators.
"""

from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd
import pandas as pd
import rasterio
from shapely.geometry import box

from src.config.platform_config import load_platform_config
from src.datasets.unified_dataset import DEFAULT_SOURCES

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "outputs" / "final_submission_data"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def _find_tiff_for_stem(stem: str):
    for src in DEFAULT_SOURCES:
        tiff_dir = ROOT / str(src["tiff_dir"])
        for ext in ("*.tif", "*.tiff"):
            for path in tiff_dir.glob(ext):
                if path.stem == stem:
                    return src, path
    return None, None


def _read_layer(shp_path: Path, target_crs):
    gdf = gpd.read_file(shp_path)
    if gdf.empty:
        return gdf
    gdf = gdf[gdf.geometry.notnull() & ~gdf.geometry.is_empty]
    if gdf.empty:
        return gdf
    return gdf.to_crs(target_crs)


def _clip_area(gdf: gpd.GeoDataFrame, clip_geom):
    if gdf.empty:
        return 0.0, 0
    intersects = gdf[gdf.geometry.intersects(clip_geom)]
    if intersects.empty:
        return 0.0, 0
    clipped = gpd.clip(intersects, gpd.GeoDataFrame(geometry=[clip_geom], crs=intersects.crs))
    if clipped.empty:
        return 0.0, 0
    return float(clipped.geometry.area.sum()), int(len(clipped))


def main() -> int:
    cfg = load_platform_config()

    rows = []
    for stem in cfg.val_tiffs:
        src, tiff_path = _find_tiff_for_stem(stem)
        if tiff_path is None:
            continue

        source_name = str(src["name"])
        shp_dir = ROOT / str(src["shp_dir"])

        built_name = "Built_Up_Area_typ.shp" if source_name == "PB" else "Built_Up_Area_type.shp"

        with rasterio.open(tiff_path) as ds:
            village_geom = box(ds.bounds.left, ds.bounds.bottom, ds.bounds.right, ds.bounds.top)
            village_area_m2 = float(village_geom.area)
            village_area_ha = village_area_m2 / 10000.0
            village_area_km2 = village_area_m2 / 1_000_000.0

            road_gdf = _read_layer(shp_dir / "Road.shp", ds.crs)
            built_gdf = _read_layer(shp_dir / built_name, ds.crs)
            water_gdf = _read_layer(shp_dir / "Water_Body.shp", ds.crs)

            road_area, road_segments = _clip_area(road_gdf, village_geom)
            built_area, built_polys = _clip_area(built_gdf, village_geom)
            water_area, water_bodies = _clip_area(water_gdf, village_geom)

            road_cov = 100.0 * road_area / village_area_m2 if village_area_m2 > 0 else 0.0
            built_cov = 100.0 * built_area / village_area_m2 if village_area_m2 > 0 else 0.0
            water_cov = 100.0 * water_area / village_area_m2 if village_area_m2 > 0 else 0.0

            infra_density = road_cov + built_cov
            built_density_ha = built_polys / village_area_ha if village_area_ha > 0 else 0.0
            water_density_km2 = water_bodies / village_area_km2 if village_area_km2 > 0 else 0.0

            land_use_indicators = {
                "impervious_index_pct": infra_density,
                "blue_infra_pct": water_cov,
                "settlement_intensity_buildings_per_ha": built_density_ha,
                "surface_pressure_ratio_built_to_water": (built_cov / water_cov) if water_cov > 0 else None,
            }

            rows.append(
                {
                    "village_stem": stem,
                    "source": source_name,
                    "tiff": tiff_path.name,
                    "area_m2": village_area_m2,
                    "area_ha": village_area_ha,
                    "road_coverage_pct": road_cov,
                    "builtup_coverage_pct": built_cov,
                    "water_coverage_pct": water_cov,
                    "infrastructure_density_pct": infra_density,
                    "road_segments_count": road_segments,
                    "builtup_polygons_count": built_polys,
                    "water_bodies_count": water_bodies,
                    "building_density_per_ha": built_density_ha,
                    "water_body_density_per_km2": water_density_km2,
                    "impervious_index_pct": land_use_indicators["impervious_index_pct"],
                    "blue_infra_pct": land_use_indicators["blue_infra_pct"],
                    "settlement_intensity_buildings_per_ha": land_use_indicators["settlement_intensity_buildings_per_ha"],
                    "surface_pressure_ratio_built_to_water": land_use_indicators["surface_pressure_ratio_built_to_water"],
                }
            )

    df = pd.DataFrame(rows)
    df.to_csv(OUT_DIR / "stakeholder_impact_metrics.csv", index=False)
    (OUT_DIR / "stakeholder_impact_metrics.json").write_text(df.to_json(orient="records", indent=2), encoding="utf-8")
    print(f"Wrote {len(df)} village rows to {OUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
