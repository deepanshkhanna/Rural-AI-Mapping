"""Sliding-window tiling utilities for large orthomosaic inference."""

from __future__ import annotations

from typing import Iterator

import numpy as np
import torch


def tile_positions(size: int, patch: int, stride: int) -> list[int]:
    """Return top-left pixel positions covering [0, size) with edge clamp."""
    if size <= patch:
        return [0]
    pos = list(range(0, max(1, size - patch + 1), stride))
    if not pos or pos[-1] + patch < size:
        pos.append(max(0, size - patch))
    return pos


def normalize_patch_rgb(patch_rgb: np.ndarray, mean: np.ndarray, std: np.ndarray) -> torch.Tensor:
    """uint8 HWC -> CHW float32 tensor with ImageNet normalization."""
    x = patch_rgb.astype(np.float32) / 255.0
    x = (x - mean) / std
    return torch.from_numpy(x.transpose(2, 0, 1))


def count_tiles(height: int, width: int, patch_size: int, overlap: int) -> int:
    """Number of sliding-window tiles for ETA estimation."""
    stride = max(1, patch_size - overlap)
    return len(tile_positions(height, patch_size, stride)) * len(tile_positions(width, patch_size, stride))


def iter_tiles(
    image_rgb: np.ndarray,
    patch_size: int,
    overlap: int,
) -> Iterator[tuple[int, int, np.ndarray, int, int]]:
    """
    Yield (row, col, patch_rgb, valid_h, valid_w) for sliding-window inference.

    Patches smaller than patch_size at raster edges are zero-padded to patch_size.
    valid_h/valid_w are the non-padded region size within the patch.
    """
    h, w = image_rgb.shape[:2]
    stride = max(1, patch_size - overlap)
    for r in tile_positions(h, patch_size, stride):
        for c in tile_positions(w, patch_size, stride):
            r_end = min(r + patch_size, h)
            c_end = min(c + patch_size, w)
            patch = image_rgb[r:r_end, c:c_end]
            ph, pw = patch.shape[:2]
            if ph < patch_size or pw < patch_size:
                padded = np.zeros((patch_size, patch_size, 3), dtype=np.uint8)
                padded[:ph, :pw] = patch
                patch = padded
            yield r, c, patch, ph, pw


def accumulate_logits(
    logit_acc: np.ndarray,
    count_acc: np.ndarray,
    logits_patch: np.ndarray,
    row: int,
    col: int,
    valid_h: int,
    valid_w: int,
) -> None:
    """Add a (C, PH, PW) logits patch into full-raster accumulators."""
    logit_acc[:, row : row + valid_h, col : col + valid_w] += logits_patch[:, :valid_h, :valid_w]
    count_acc[row : row + valid_h, col : col + valid_w] += 1.0


def finalize_logits(logit_acc: np.ndarray, count_acc: np.ndarray) -> np.ndarray:
    """Average overlapping tile logits."""
    count_acc = np.maximum(count_acc, 1.0)
    for cls in range(logit_acc.shape[0]):
        logit_acc[cls] /= count_acc
    return logit_acc
