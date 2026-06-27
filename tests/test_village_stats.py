"""Tests for village infrastructure statistics."""

import numpy as np

from src.inference.village_stats import VillageReport


def test_village_report_physical_units_from_gsd():
    mask = np.zeros((100, 100), dtype=np.uint8)
    mask[10:20, 10:90] = 1   # road
    mask[40:60, 40:60] = 4   # water
    mask[70:80, 70:80] = 3   # built-up

    gsd = 0.5
    report = VillageReport.from_mask(mask, pixel_size_m=gsd, village_name="Test")
    assert report.pixel_size_m == gsd
    assert report.water.area_m2 == round((20 * 20) * gsd * gsd, 1)
