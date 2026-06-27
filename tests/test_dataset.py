"""Tests for UnifiedMultiClassDataset with synthetic fixtures."""

import numpy as np
import torch

from src.datasets.unified_dataset import UnifiedMultiClassDataset, get_val_transform


def test_synthetic_val_dataset_loads():
    ds = UnifiedMultiClassDataset(
        split="val",
        transform=get_val_transform(256),
        patch_size=256,
        patches_per_image=4,
        train_tiffs=["SYNTHETIC_TEST_ORTHO"],
        val_tiffs=["SYNTHETIC_TEST_ORTHO"],
    )
    assert len(ds) > 0
    image, mask = ds[0]
    assert isinstance(image, torch.Tensor)
    assert image.shape[0] == 3
    assert mask.dtype == torch.long
    assert mask.shape[0] == 256
    assert mask.shape[1] == 256


def test_rasterize_empty_layers():
    from rasterio.transform import from_origin
    from rasterio.windows import Window
    from src.datasets.unified_dataset import UnifiedMultiClassDataset

    mask = UnifiedMultiClassDataset._rasterize_patch(
        Window(0, 0, 8, 8),
        from_origin(0, 8, 1, 1),
        {},
        patch_size=8,
    )
    assert mask.shape == (8, 8)
    assert mask.sum() == 0
