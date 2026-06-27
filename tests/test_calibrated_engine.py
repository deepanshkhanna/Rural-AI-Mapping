"""Tests for CalibratedEngine inference API."""

from pathlib import Path

import numpy as np
import torch

from src.inference.calibrated_engine import CalibratedEngine, pixel_size_from_transform
from rasterio.transform import from_origin


def test_pixel_size_from_transform():
    t = from_origin(0, 0, 0.5, 0.5)
    assert pixel_size_from_transform(t) == 0.5


def test_predict_batch_returns_logits_based_postprocess():
    root = Path(__file__).resolve().parents[1]
    engine = CalibratedEngine.from_checkpoints(
        root / "outputs/checkpoints/best_model.pth",
        root / "outputs/checkpoints/latest_model.pth",
        device="cpu",
        use_tta=False,
    )
    x = torch.randn(1, 3, 128, 128)
    preds, probs = engine.predict_batch(x, postprocess=True)
    assert preds.shape == (1, 128, 128)
    assert probs.shape == (1, 5, 128, 128)


def test_predict_large_sliding_window():
    root = Path(__file__).resolve().parents[1]
    engine = CalibratedEngine.from_checkpoints(
        root / "outputs/checkpoints/best_model.pth",
        root / "outputs/checkpoints/latest_model.pth",
        device="cpu",
        use_tta=False,
    )
    img = np.random.randint(0, 255, (600, 800, 3), dtype=np.uint8)
    mask, logits = engine.predict_large(img, patch_size=256, overlap=32, postprocess=False)
    assert mask.shape == (600, 800)
    assert logits.shape == (5, 600, 800)


def test_predict_tiff_preserves_crs(tmp_path):
    root = Path(__file__).resolve().parents[1]
    tiff = root / "tests/fixtures/synthetic/tiffs/SYNTHETIC_TEST_ORTHO.tif"
    if not tiff.exists():
        return

    engine = CalibratedEngine.from_checkpoints(
        root / "outputs/checkpoints/best_model.pth",
        root / "outputs/checkpoints/latest_model.pth",
        device="cpu",
        use_tta=False,
    )
    out = tmp_path / "mask.tif"
    mask, meta = engine.predict_tiff(tiff, output_path=out, patch_size=256, overlap=32)
    assert mask.shape == (meta["height"], meta["width"])
    assert meta["epsg"] == 32643
    assert out.exists()
