"""Dataset remediation pipeline for Phase 2 transformation.

Outputs:
- outputs/recovery_reports/data_asset_forensics_report.md
- outputs/recovery_reports/dataset_truth_report.md
- outputs/recovery_reports/geometry_repair_report.md
- outputs/recovery_reports/corrupt_asset_quarantine_report.md
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path

import geopandas as gpd
import rasterio
from shapely.geometry import GeometryCollection, MultiPolygon, Polygon
from shapely.geometry import box
from shapely.geometry.base import BaseGeometry
from shapely.validation import make_valid

from src.datasets.unified_dataset import DEFAULT_SOURCES


OUT_DIR = Path("outputs/recovery_reports")
QUARANTINE_DIR = Path("data/quarantine/corrupt_tiffs")


@dataclass
class RasterIssue:
    source: str
    path: str
    error: str


@dataclass
class GeometryIssue:
    source: str
    path: str
    invalid_count: int
    empty_count: int
    duplicate_count: int


def _safe_make_valid(geom: BaseGeometry | None) -> BaseGeometry | None:
    if geom is None:
        return None
    if geom.is_empty:
        return geom
    if geom.is_valid:
        return geom
    fixed = make_valid(geom)
    if fixed.is_empty:
        return fixed
    if not fixed.is_valid:
        fixed = fixed.buffer(0)
    return fixed


def _extract_polygonal(geom: BaseGeometry | None) -> BaseGeometry | None:
    if geom is None:
        return None
    if geom.is_empty:
        return geom
    if isinstance(geom, (Polygon, MultiPolygon)):
        return geom
    if isinstance(geom, GeometryCollection):
        polys = [g for g in geom.geoms if isinstance(g, (Polygon, MultiPolygon)) and not g.is_empty]
        if not polys:
            return None
        # Normalize to MultiPolygon when multiple pieces exist.
        parts = []
        for p in polys:
            if isinstance(p, Polygon):
                parts.append(p)
            elif isinstance(p, MultiPolygon):
                parts.extend(list(p.geoms))
        return MultiPolygon(parts) if len(parts) > 1 else parts[0]
    return None


def scan_rasters() -> tuple[list[dict], list[dict]]:
    ok = []
    bad = []
    for source in DEFAULT_SOURCES:
        name = source["name"]
        tiff_dir = Path(source["tiff_dir"])
        tiffs = sorted(list(tiff_dir.glob("*.tif")) + list(tiff_dir.glob("*.tiff")))
        for tif in tiffs:
            try:
                with rasterio.open(tif) as src:
                    ok.append(
                        {
                            "source": name,
                            "path": str(tif),
                            "width": src.width,
                            "height": src.height,
                            "crs": str(src.crs),
                            "transform": tuple(src.transform)[:6],
                            "bands": src.count,
                        }
                    )
            except Exception as exc:
                bad.append(asdict(RasterIssue(source=name, path=str(tif), error=str(exc))))
    return ok, bad


def scan_vectors() -> list[dict]:
    out = []
    for source in DEFAULT_SOURCES:
        name = source["name"]
        shp_dir = Path(source["shp_dir"])
        for shp_name in source["class_mapping"].keys():
            shp = shp_dir / shp_name
            if not shp.exists():
                out.append(
                    asdict(
                        GeometryIssue(
                            source=name,
                            path=str(shp),
                            invalid_count=-1,
                            empty_count=-1,
                            duplicate_count=-1,
                        )
                    )
                )
                continue

            gdf = gpd.read_file(shp)
            empty_count = int(gdf.geometry.is_empty.sum())
            invalid_count = int((~gdf.geometry.is_valid).sum())
            dup_count = int(gdf.geometry.astype(str).duplicated().sum())
            out.append(
                asdict(
                    GeometryIssue(
                        source=name,
                        path=str(shp),
                        invalid_count=invalid_count,
                        empty_count=empty_count,
                        duplicate_count=dup_count,
                    )
                )
            )
    return out


def write_forensics_report(raster_bad: list[dict], geom_issues: list[dict]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    md = OUT_DIR / "data_asset_forensics_report.md"
    lines = [
        "# Data Asset Forensics Report",
        "",
        "## Corrupt / Unreadable Rasters",
    ]
    if not raster_bad:
        lines.append("- None")
    else:
        for row in raster_bad:
            lines.extend(
                [
                    f"- filename: {row['path']}",
                    f"  error: {row['error']}",
                    "  root cause: unreadable TIFF directory/offset corruption",
                    "  recoverable?: no (not via metadata patch in this repo)",
                    "  replacement required?: yes",
                    "  repair strategy: quarantine corrupt file and request source re-export",
                ]
            )

    lines.extend(["", "## Vector Integrity Findings"])
    any_issue = False
    for row in geom_issues:
        if row["invalid_count"] > 0 or row["empty_count"] > 0 or row["duplicate_count"] > 0:
            any_issue = True
            lines.extend(
                [
                    f"- filename: {row['path']}",
                    f"  invalid geometries: {row['invalid_count']}",
                    f"  empty geometries: {row['empty_count']}",
                    f"  duplicate geometries: {row['duplicate_count']}",
                    "  root cause: annotation geometry quality defects",
                    "  recoverable?: yes (auto-repair + de-dup)",
                    "  replacement required?: no if repaired geometry validates",
                    "  repair strategy: make_valid/buffer(0), drop empties, drop duplicates",
                ]
            )
    if not any_issue:
        lines.append("- None")

    md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {md}")


def auto_repair_vectors(apply: bool) -> dict:
    repairs = []
    for source in DEFAULT_SOURCES:
        shp_dir = Path(source["shp_dir"])
        for shp_name in source["class_mapping"].keys():
            shp = shp_dir / shp_name
            if not shp.exists():
                continue
            gdf = gpd.read_file(shp)

            before_invalid = int((~gdf.geometry.is_valid).sum())
            before_empty = int(gdf.geometry.is_empty.sum())
            before_dup = int(gdf.geometry.astype(str).duplicated().sum())

            if before_invalid == 0 and before_empty == 0 and before_dup == 0:
                continue

            gdf["geometry"] = gdf.geometry.apply(_safe_make_valid)
            # Preserve polygon layer type for target shapefiles.
            gdf["geometry"] = gdf.geometry.apply(_extract_polygonal)
            gdf = gdf[gdf.geometry.notnull()].copy()
            gdf = gdf[~gdf.geometry.is_empty].copy()
            gdf = gdf.drop_duplicates(subset="geometry")

            after_invalid = int((~gdf.geometry.is_valid).sum())
            after_empty = int(gdf.geometry.is_empty.sum())
            after_dup = int(gdf.geometry.astype(str).duplicated().sum())

            if apply:
                gdf.to_file(shp)

            repairs.append(
                {
                    "path": str(shp),
                    "before": {
                        "invalid": before_invalid,
                        "empty": before_empty,
                        "duplicate": before_dup,
                    },
                    "after": {
                        "invalid": after_invalid,
                        "empty": after_empty,
                        "duplicate": after_dup,
                    },
                }
            )

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_json = OUT_DIR / "geometry_repair_report.json"
    out_md = OUT_DIR / "geometry_repair_report.md"
    out_json.write_text(json.dumps({"apply": apply, "repairs": repairs}, indent=2), encoding="utf-8")

    lines = ["# Geometry Repair Report", f"- Apply mode: {apply}", f"- Repaired files: {len(repairs)}", ""]
    for r in repairs:
        lines.append(f"- {r['path']}")
        lines.append(
            f"  before: invalid={r['before']['invalid']} empty={r['before']['empty']} duplicate={r['before']['duplicate']}"
        )
        lines.append(
            f"  after:  invalid={r['after']['invalid']} empty={r['after']['empty']} duplicate={r['after']['duplicate']}"
        )
    if not repairs:
        lines.append("- No repairs needed")
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {out_json}")
    print(f"Wrote {out_md}")
    return {"apply": apply, "repairs": repairs}


def quarantine_corrupt_rasters(raster_bad: list[dict], apply: bool) -> dict:
    actions = []
    QUARANTINE_DIR.mkdir(parents=True, exist_ok=True)
    for row in raster_bad:
        src = Path(row["path"])
        if not src.exists():
            continue
        dst = QUARANTINE_DIR / src.name
        actions.append({"from": str(src), "to": str(dst)})
        if apply:
            src.rename(dst)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_json = OUT_DIR / "corrupt_asset_quarantine_report.json"
    out_md = OUT_DIR / "corrupt_asset_quarantine_report.md"
    out_json.write_text(json.dumps({"apply": apply, "moved": actions}, indent=2), encoding="utf-8")

    lines = ["# Corrupt Asset Quarantine Report", f"- Apply mode: {apply}", f"- Moved files: {len(actions)}", ""]
    for a in actions:
        lines.append(f"- {a['from']} -> {a['to']}")
    if not actions:
        lines.append("- No corrupt files found")
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {out_json}")
    print(f"Wrote {out_md}")
    return {"apply": apply, "moved": actions}


def dataset_truth_report() -> None:
    # Vector-derived truth report from source annotations and raster pixel sizes.
    # This is deterministic and recomputed from raw source files.
    total_tiffs = 0
    total_polygons = 0
    class_area_m2 = {1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0}
    class_px_est = {1: 0, 2: 0, 3: 0, 4: 0}
    village_names = set()
    shp_cache: dict[tuple[str, str], gpd.GeoDataFrame] = {}

    for source in DEFAULT_SOURCES:
        tiff_dir = Path(source["tiff_dir"])
        shp_dir = Path(source["shp_dir"])
        class_map = source["class_mapping"]

        tiffs = sorted(list(tiff_dir.glob("*.tif")) + list(tiff_dir.glob("*.tiff")))
        total_tiffs += len(tiffs)
        for tif in tiffs:
            village_names.add(tif.stem)
            try:
                with rasterio.open(tif) as src:
                    pixel_area = abs(src.transform.a * src.transform.e)
                    raster_crs = src.crs
                    rb = src.bounds
            except Exception:
                continue

            tif_poly = box(rb.left, rb.bottom, rb.right, rb.top)

            for shp_name, cls in class_map.items():
                shp = shp_dir / shp_name
                if not shp.exists():
                    continue
                cache_key = (str(shp), str(raster_crs))
                if cache_key not in shp_cache:
                    gdf = gpd.read_file(shp)
                    if gdf.crs is None:
                        shp_cache[cache_key] = gdf.iloc[0:0].copy()
                    else:
                        if str(gdf.crs) != str(raster_crs):
                            gdf = gdf.to_crs(raster_crs)
                        shp_cache[cache_key] = gdf

                gdf = shp_cache[cache_key]
                if gdf.empty:
                    continue

                # Clip to TIFF bounds to avoid counting features outside the raster.
                clipped = gdf.cx[rb.left:rb.right, rb.bottom:rb.top].copy()
                if clipped.empty:
                    continue

                clipped["geometry"] = clipped.geometry.intersection(tif_poly)
                clipped = clipped[~clipped.geometry.is_empty]
                if clipped.empty:
                    continue

                total_polygons += int(len(clipped))
                area_m2 = float(clipped.geometry.area.sum())
                class_area_m2[cls] += area_m2
                if pixel_area > 0:
                    class_px_est[cls] += int(area_m2 / pixel_area)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    md = OUT_DIR / "dataset_truth_report.md"
    lines = [
        "# Dataset Truth Report",
        "",
        f"- total villages: {len(village_names)}",
        f"- total TIFFs: {total_tiffs}",
        f"- total polygons: {total_polygons}",
        "",
        "## Class Pixel Distribution (vector-derived estimate from source geometries)",
        f"- road pixels (est): {class_px_est[1]:,}",
        f"- bridge pixels (est): {class_px_est[2]:,}",
        f"- built-up pixels (est): {class_px_est[3]:,}",
        f"- water pixels (est): {class_px_est[4]:,}",
        "",
        "## Class Area Distribution",
        f"- road area m2: {class_area_m2[1]:,.2f}",
        f"- bridge area m2: {class_area_m2[2]:,.2f}",
        f"- built-up area m2: {class_area_m2[3]:,.2f}",
        f"- water area m2: {class_area_m2[4]:,.2f}",
    ]
    md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {md}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Dataset remediation pipeline")
    parser.add_argument("--apply", action="store_true", help="Apply repair/quarantine actions")
    args = parser.parse_args()

    raster_ok, raster_bad = scan_rasters()
    geom_issues = scan_vectors()
    write_forensics_report(raster_bad, geom_issues)
    auto_repair_vectors(apply=args.apply)

    # Re-scan rasters after potential repair stage; then quarantine corrupt assets.
    _, raster_bad_post = scan_rasters()
    quarantine_corrupt_rasters(raster_bad_post, apply=args.apply)

    # Final truth report from current source state.
    dataset_truth_report()

    # Persist machine-readable summary.
    summary = {
        "apply": args.apply,
        "readable_rasters": len(raster_ok),
        "corrupt_rasters": len(raster_bad_post),
        "geometry_issue_files": sum(
            1
            for x in geom_issues
            if x["invalid_count"] > 0 or x["empty_count"] > 0 or x["duplicate_count"] > 0
        ),
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "dataset_remediation_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Wrote {OUT_DIR / 'dataset_remediation_summary.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
