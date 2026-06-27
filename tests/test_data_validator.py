from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.transform import from_origin
from shapely.geometry import Polygon

import src.data_validation.validator as validator
from src.data_validation.validator import ValidationIssue, ValidationReport


class StubCfg:
    geospatial = {"allowed_epsg": [32643, 32644]}


def _write_tiff(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    arr = np.zeros((1, 16, 16), dtype=np.uint8)
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=16,
        width=16,
        count=1,
        dtype=arr.dtype,
        crs="EPSG:32643",
        transform=from_origin(0, 16, 1, 1),
    ) as dst:
        dst.write(arr)


def _write_tiff_epsg(path: Path, epsg: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    arr = np.zeros((1, 16, 16), dtype=np.uint8)
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=16,
        width=16,
        count=1,
        dtype=arr.dtype,
        crs=epsg,
        transform=from_origin(0, 16, 1, 1),
    ) as dst:
        dst.write(arr)


def _write_shp(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    gdf = gpd.GeoDataFrame({"id": [1]}, geometry=[Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])], crs="EPSG:32643")
    gdf.to_file(path)


def test_dataset_validator_pass(monkeypatch, tmp_path: Path):
    tiff_dir = tmp_path / "tiffs"
    shp_dir = tmp_path / "shp"
    _write_tiff(tiff_dir / "x.tif")
    _write_shp(shp_dir / "Road.shp")
    _write_shp(shp_dir / "Bridge.shp")
    _write_shp(shp_dir / "Built_Up_Area_typ.shp")
    _write_shp(shp_dir / "Water_Body.shp")

    monkeypatch.setattr(validator, "load_platform_config", lambda: StubCfg())
    monkeypatch.setattr(validator, "get_default_sources", lambda: [
            {
                "name": "TEST",
                "tiff_dir": str(tiff_dir),
                "shp_dir": str(shp_dir),
                "class_mapping": {
                    "Road.shp": 1,
                    "Bridge.shp": 2,
                    "Built_Up_Area_typ.shp": 3,
                    "Water_Body.shp": 4,
                },
            },
    ])

    rep = validator.DatasetValidator().run()
    assert rep.ok
    assert rep.scanned_tiffs == 1


def test_dataset_validator_fails_missing_bridge(monkeypatch, tmp_path: Path):
    tiff_dir = tmp_path / "tiffs"
    shp_dir = tmp_path / "shp"
    _write_tiff(tiff_dir / "x.tif")
    _write_shp(shp_dir / "Road.shp")
    _write_shp(shp_dir / "Built_Up_Area_typ.shp")
    _write_shp(shp_dir / "Water_Body.shp")

    monkeypatch.setattr(validator, "load_platform_config", lambda: StubCfg())
    monkeypatch.setattr(validator, "get_default_sources", lambda: [
            {
                "name": "TEST",
                "tiff_dir": str(tiff_dir),
                "shp_dir": str(shp_dir),
                "class_mapping": {
                    "Road.shp": 1,
                    "Bridge.shp": 2,
                    "Built_Up_Area_typ.shp": 3,
                    "Water_Body.shp": 4,
                },
            },
    ])

    rep = validator.DatasetValidator().run()
    assert not rep.ok
    assert rep.issues


def test_dataset_validator_flags_unexpected_epsg(monkeypatch, tmp_path: Path):
    tiff_dir = tmp_path / "tiffs"
    shp_dir = tmp_path / "shp"
    _write_tiff_epsg(tiff_dir / "x.tif", "EPSG:4326")
    _write_shp(shp_dir / "Road.shp")
    _write_shp(shp_dir / "Bridge.shp")
    _write_shp(shp_dir / "Built_Up_Area_typ.shp")
    _write_shp(shp_dir / "Water_Body.shp")

    monkeypatch.setattr(validator, "load_platform_config", lambda: StubCfg())
    monkeypatch.setattr(validator, "get_default_sources", lambda: [
            {
                "name": "TEST",
                "tiff_dir": str(tiff_dir),
                "shp_dir": str(shp_dir),
                "class_mapping": {
                    "Road.shp": 1,
                    "Bridge.shp": 2,
                    "Built_Up_Area_typ.shp": 3,
                    "Water_Body.shp": 4,
                },
            },
    ])

    rep = validator.DatasetValidator().run()
    assert not rep.ok
    assert any(i.category == "crs" for i in rep.issues)


def test_validator_main_writes_reports(monkeypatch, tmp_path: Path):
    fake = ValidationReport(
        ok=True,
        scanned_tiffs=1,
        scanned_shapefiles=4,
        issues=[ValidationIssue("high", "test", "S", "A", "M")],
    )

    class StubRunner:
        def run(self):
            return fake

    monkeypatch.setattr(validator, "DatasetValidator", StubRunner)
    monkeypatch.chdir(tmp_path)

    rc = validator.main()
    assert rc == 0
    assert (tmp_path / "outputs/recovery_reports/dataset_validation_report.md").exists()
    assert (tmp_path / "outputs/recovery_reports/dataset_validation_report.json").exists()
