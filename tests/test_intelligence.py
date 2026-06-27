"""Tests for spatial intelligence and survey reports."""

import numpy as np

from src.intelligence.spatial_analysis import analyze_spatial_intelligence
from src.intelligence.survey_report import build_survey_intelligence


def test_spatial_intelligence_road_access():
    mask = np.zeros((200, 200), dtype=np.uint8)
    mask[100, 50:150] = 1  # horizontal road
    mask[80:120, 120:180] = 3  # built-up near road
    intel = analyze_spatial_intelligence(mask, pixel_size_m=0.5)
    assert intel.road_connected_components >= 1
    assert intel.builtup_road_access_pct > 0
    assert len(intel.recommendations) >= 1


def test_survey_intelligence_report():
    mask = np.zeros((64, 64), dtype=np.uint8)
    mask[20:25, 10:50] = 1
    mask[30:45, 30:45] = 4
    logits = np.random.randn(5, 64, 64).astype(np.float32)
    report = build_survey_intelligence(mask, pixel_size_m=0.5, logits=logits)
    assert report.executive_summary
    d = report.to_dict()
    assert "spatial_intelligence" in d
    assert "field_verification" in d
