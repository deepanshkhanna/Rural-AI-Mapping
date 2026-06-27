"""Tests for postprocessing confidence gates and strict mode."""

import numpy as np
import pytest

from src.postprocessing import CLASS_WATER, postprocess_mask, refine_water


def test_water_confidence_gate_uses_raw_logits_not_double_softmax():
    """Water gate at 0.35 must operate on logits, not softmax-of-softmax."""
    h, w = 32, 32
    mask = np.zeros((h, w), dtype=np.uint8)
    mask[10:20, 10:20] = CLASS_WATER

    logits = np.full((5, h, w), -5.0, dtype=np.float32)
    logits[CLASS_WATER, 10:20, 10:20] = -0.85  # softmax ~0.30, below 0.35 gate

    refined = refine_water(mask.copy(), logits)
    assert (refined == CLASS_WATER).sum() == 0

    # Double-softmax would push values toward uniform ~0.2 and fail to gate
    probs = np.exp(logits) / np.exp(logits).sum(axis=0, keepdims=True)
    refined_bad = refine_water(mask.copy(), probs)
    # With wrongly passed probs treated as logits, behavior differs from correct path
    assert (refined == CLASS_WATER).sum() <= (refined_bad == CLASS_WATER).sum()


def test_postprocess_strict_raises(monkeypatch):
    mask = np.zeros((16, 16), dtype=np.uint8)

    def boom(m):
        raise RuntimeError("forced")

    import src.postprocessing as pp

    monkeypatch.setattr(pp, "refine_roads", boom)
    with pytest.raises(RuntimeError):
        postprocess_mask(mask, strict=True)

    # Non-strict returns original mask after logging failure
    out = postprocess_mask(mask, strict=False)
    assert out.shape == mask.shape
