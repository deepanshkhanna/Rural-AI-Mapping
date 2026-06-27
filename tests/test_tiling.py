"""Tests for sliding-window tiling utilities."""

import numpy as np

from src.inference.tiling import (
    accumulate_logits,
    finalize_logits,
    iter_tiles,
    tile_positions,
)


def test_tile_positions_cover_edges():
    pos = tile_positions(1000, 768, 640)
    assert pos[0] == 0
    assert pos[-1] + 768 >= 1000


def test_iter_tiles_and_accumulate():
    img = np.random.randint(0, 255, (900, 1100, 3), dtype=np.uint8)
    h, w = img.shape[:2]
    logit_acc = np.zeros((5, h, w), dtype=np.float32)
    count_acc = np.zeros((h, w), dtype=np.float32)

    for r, c, _patch, ph, pw in iter_tiles(img, patch_size=256, overlap=32):
        fake_logits = np.ones((5, 256, 256), dtype=np.float32)
        accumulate_logits(logit_acc, count_acc, fake_logits, r, c, ph, pw)

    logit_acc = finalize_logits(logit_acc, count_acc)
    assert logit_acc.shape == (5, h, w)
    assert np.all(logit_acc > 0)
