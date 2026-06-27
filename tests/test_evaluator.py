"""Tests for evaluation metric math."""

import numpy as np

from src.evaluation.unified_evaluator import compute_counts_metrics


def test_compute_counts_metrics_basic():
    tp = np.array([0, 80, 0, 50, 90], dtype=np.int64)
    gt = np.array([0, 100, 0, 100, 100], dtype=np.int64)
    pr = np.array([0, 90, 0, 60, 95], dtype=np.int64)
    names = {0: "Background", 1: "Road", 2: "Bridge", 3: "Built-Up Area", 4: "Water Body"}

    out = compute_counts_metrics(tp, gt, pr, names)
    assert "fg_miou" in out
    assert out["Road"]["iou"] == round(80 / (100 + 90 - 80 + 1e-10), 4)
    assert out["Road"]["recall"] == 0.8
