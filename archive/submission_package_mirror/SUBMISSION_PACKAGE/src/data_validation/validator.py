"""Blocking dataset validation framework for geospatial assets."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

import geopandas as gpd
import rasterio

from src.config.platform_config import load_platform_config
from src.datasets.unified_dataset import get_default_sources


@dataclass
class ValidationIssue:
    severity: str
    category: str
    source: str
    asset: str
    message: str


@dataclass
class ValidationReport:
    ok: bool
    scanned_tiffs: int
    scanned_shapefiles: int
    issues: list[ValidationIssue] = field(default_factory=list)

    def to_json(self) -> dict:
        return {
            "ok": self.ok,
            "scanned_tiffs": self.scanned_tiffs,
            "scanned_shapefiles": self.scanned_shapefiles,
            "issues": [asdict(i) for i in self.issues],
        }


class DatasetValidator:
    def __init__(self) -> None:
        self.cfg = load_platform_config()
        self.allowed_epsg = {int(v) for v in self.cfg.geospatial.get("allowed_epsg", [])}

    def run(self) -> ValidationReport:
        issues: list[ValidationIssue] = []
        scanned_tiffs = 0
        scanned_shp = 0

        for source in get_default_sources():
            source_name = source["name"]
            tiff_dir = Path(source["tiff_dir"])
            shp_dir = Path(source["shp_dir"])

            ext_cfg = self.cfg.geospatial.get("raster_extensions", [".tif", ".tiff"])
            tiffs: list[Path] = []
            for ext in ext_cfg:
                tiffs.extend(tiff_dir.glob(f"*{ext}"))
            tiffs = sorted(set(tiffs))
            for tif in tiffs:
                scanned_tiffs += 1
                try:
                    with rasterio.open(tif) as src:
                        _ = src.bounds
                        if src.crs is None:
                            issues.append(
                                ValidationIssue("critical", "crs", source_name, str(tif), "Missing CRS")
                            )
                        elif src.crs.to_epsg() not in self.allowed_epsg:
                            issues.append(
                                ValidationIssue(
                                    "high",
                                    "crs",
                                    source_name,
                                    str(tif),
                                    f"Unexpected EPSG: {src.crs.to_epsg()} (allowed: {sorted(self.allowed_epsg)})",
                                )
                            )
                except Exception as exc:
                    issues.append(
                        ValidationIssue("critical", "integrity", source_name, str(tif), f"Unreadable TIFF: {exc}")
                    )

            for shp_name in source["class_mapping"].keys():
                shp_path = shp_dir / shp_name
                scanned_shp += 1
                if not shp_path.exists():
                    issues.append(
                        ValidationIssue("critical", "annotation", source_name, str(shp_path), "Missing shapefile")
                    )
                    continue

                try:
                    gdf = gpd.read_file(shp_path)
                    if gdf.empty:
                        issues.append(
                            ValidationIssue("high", "annotation", source_name, str(shp_path), "Shapefile has 0 features")
                        )
                    if gdf.crs is None:
                        issues.append(
                            ValidationIssue("critical", "annotation", source_name, str(shp_path), "Shapefile CRS missing")
                        )
                    invalid = (~gdf.geometry.is_valid).sum()
                    if invalid > 0:
                        issues.append(
                            ValidationIssue(
                                "high",
                                "geometry",
                                source_name,
                                str(shp_path),
                                f"Invalid geometries: {int(invalid)}",
                            )
                        )
                except Exception as exc:
                    issues.append(
                        ValidationIssue("critical", "annotation", source_name, str(shp_path), f"Unreadable shapefile: {exc}")
                    )

        ok = not any(i.severity in {"critical", "high"} for i in issues)
        return ValidationReport(ok=ok, scanned_tiffs=scanned_tiffs, scanned_shapefiles=scanned_shp, issues=issues)


def main() -> int:
    report = DatasetValidator().run()
    out_dir = Path("outputs/recovery_reports")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_json = out_dir / "dataset_validation_report.json"
    out_md = out_dir / "dataset_validation_report.md"

    out_json.write_text(json.dumps(report.to_json(), indent=2), encoding="utf-8")

    lines = [
        "# Dataset Validation Report",
        f"- Status: {'PASS' if report.ok else 'FAIL'}",
        f"- Scanned TIFFs: {report.scanned_tiffs}",
        f"- Scanned Shapefiles: {report.scanned_shapefiles}",
        f"- Issues: {len(report.issues)}",
        "",
        "## Issues",
    ]
    if not report.issues:
        lines.append("- None")
    else:
        for i in report.issues:
            lines.append(f"- [{i.severity.upper()}] {i.category} | {i.source} | {i.asset} | {i.message}")

    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {out_json}")
    print(f"Wrote {out_md}")
    return 0 if report.ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
