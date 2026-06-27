"""Tests for field verification priority queue."""

import numpy as np

from src.intelligence.spatial_analysis import analyze_spatial_intelligence
from src.intelligence.survey_operations import (
    build_field_verification_queue,
    compute_village_accessibility_score,
    render_field_verification_overlay,
)
from src.intelligence.survey_report import build_survey_intelligence


def test_empty_village_queue():
    mask = np.zeros((128, 128), dtype=np.uint8)
    conf = np.full((128, 128), 0.95, dtype=np.float32)
    result = build_field_verification_queue(mask, pixel_size_m=0.5, confidence_map=conf)
    assert result.field_verification_queue == []
    assert result.village_accessibility_score >= 0
    assert len(result.top_field_priorities) >= 1


def test_single_isolated_cluster_ranks_first():
    mask = np.zeros((200, 200), dtype=np.uint8)
    mask[80:140, 80:140] = 3
    conf = np.full((200, 200), 0.4, dtype=np.float32)
    result = build_field_verification_queue(mask, pixel_size_m=0.5, confidence_map=conf)
    assert len(result.field_verification_queue) >= 1
    top = result.field_verification_queue[0]
    assert top.rank == 1
    assert top.item_type == "settlement_cluster"
    assert top.access_assessment == "isolated"
    assert top.score > 50


def test_deterministic_ranking():
    mask = np.zeros((256, 256), dtype=np.uint8)
    mask[100, 40:180] = 1
    mask[60:100, 140:200] = 3
    mask[160:200, 30:90] = 3
    logits = np.random.RandomState(42).randn(5, 256, 256).astype(np.float32)
    r1 = build_field_verification_queue(mask, pixel_size_m=0.5, logits=logits)
    r2 = build_field_verification_queue(mask, pixel_size_m=0.5, logits=logits)
    assert [q.score for q in r1.field_verification_queue] == [q.score for q in r2.field_verification_queue]
    assert [q.label for q in r1.field_verification_queue] == [q.label for q in r2.field_verification_queue]


def test_score_stability_same_inputs():
    mask = np.zeros((100, 100), dtype=np.uint8)
    mask[40:70, 40:70] = 3
    conf = np.full((100, 100), 0.55, dtype=np.float32)
    scores = [
        build_field_verification_queue(mask, 0.5, confidence_map=conf).field_verification_queue[0].score
        for _ in range(3)
    ]
    assert scores[0] == scores[1] == scores[2]


def test_high_confidence_connected_lower_priority():
    mask = np.zeros((200, 200), dtype=np.uint8)
    mask[100, 30:170] = 1
    mask[85:115, 100:150] = 3
    low_conf = np.full((200, 200), 0.35, dtype=np.float32)
    high_conf = np.full((200, 200), 0.95, dtype=np.float32)
    r_low = build_field_verification_queue(mask, 0.5, confidence_map=low_conf)
    r_high = build_field_verification_queue(mask, 0.5, confidence_map=high_conf)
    assert r_low.field_verification_queue[0].score > r_high.field_verification_queue[0].score


def test_score_breakdown_present():
    mask = np.zeros((120, 120), dtype=np.uint8)
    mask[40:90, 40:90] = 3
    result = build_field_verification_queue(mask, 0.5, confidence_map=np.full((120, 120), 0.5))
    item = result.field_verification_queue[0]
    bd = item.score_breakdown
    assert "confidence_risk" in bd
    assert "isolation_risk" in bd
    assert "weights" in bd
    assert item.reason


def test_village_accessibility_score_range():
    mask = np.zeros((100, 100), dtype=np.uint8)
    mask[50, 20:80] = 1
    mask[40:60, 40:60] = 3
    spatial = analyze_spatial_intelligence(mask, 0.5)
    score = compute_village_accessibility_score(spatial)
    assert 0 <= score <= 100


def test_survey_intelligence_includes_field_verification():
    mask = np.zeros((64, 64), dtype=np.uint8)
    mask[20:45, 20:45] = 3
    logits = np.random.randn(5, 64, 64).astype(np.float32)
    report = build_survey_intelligence(mask, pixel_size_m=0.5, logits=logits)
    d = report.to_dict()
    assert "field_verification" in d
    assert "village_accessibility_score" in d["field_verification"]
    assert d["executive_summary"][0].startswith("Village Accessibility Score")


def test_render_overlay_with_queue():
    rgb = np.zeros((64, 64, 3), dtype=np.uint8)
    mask = np.zeros((64, 64), dtype=np.uint8)
    mask[20:50, 20:50] = 3
    result = build_field_verification_queue(mask, 0.5, confidence_map=np.full((64, 64), 0.4))
    out = render_field_verification_overlay(rgb, result.field_verification_queue)
    assert out.shape == rgb.shape
