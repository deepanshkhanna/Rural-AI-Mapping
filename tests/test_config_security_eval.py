from pathlib import Path
from unittest.mock import patch

import numpy as np
import torch
from torch.utils.data import DataLoader, TensorDataset

from src.config.platform_config import load_platform_config
from src.evaluation.unified_evaluator import compute_counts_metrics, evaluate_model_iou
from src.security.checkpoints import file_sha256, load_checkpoint_secure


def test_platform_config_loads():
    cfg = load_platform_config()
    assert cfg.version
    assert cfg.num_classes == 5
    assert len(cfg.train_tiffs) > 0
    assert len(cfg.val_tiffs) > 0


def test_file_sha256(tmp_path: Path):
    p = tmp_path / "x.txt"
    p.write_text("abc", encoding="utf-8")
    h = file_sha256(p)
    assert len(h) == 64


def test_load_checkpoint_secure_success(tmp_path: Path):
    p = tmp_path / "ckpt.pth"
    torch.save({"model_state_dict": {}, "config": {"classes": 5}}, p)
    ckpt = load_checkpoint_secure(p, map_location="cpu")
    assert "config" in ckpt


def test_load_checkpoint_secure_hash_mismatch(tmp_path: Path):
    p = tmp_path / "ckpt_bad.pth"
    torch.save({"a": 1}, p)
    try:
        _ = load_checkpoint_secure(p, expected_sha256="0" * 64)
        assert False, "Expected checksum mismatch"
    except RuntimeError:
        assert True


def test_load_checkpoint_secure_missing_file(tmp_path: Path):
    p = tmp_path / "nope.pth"
    try:
        _ = load_checkpoint_secure(p)
        assert False, "Expected missing-file error"
    except FileNotFoundError:
        assert True


def test_load_checkpoint_secure_unsafe_fallback_disabled(tmp_path: Path):
    p = tmp_path / "unsafe.pth"
    p.write_bytes(b"x")

    with patch("src.security.checkpoints.torch.load") as mock_load:
        mock_load.side_effect = RuntimeError("safe load failed")
        try:
            _ = load_checkpoint_secure(p)
            assert False, "Expected strict secure load failure"
        except RuntimeError as exc:
            assert "Unsafe fallback is disabled by policy" in str(exc)


def test_compute_counts_metrics_bridge_key():
    class_names = {0: "Background", 1: "Road", 2: "Bridge", 3: "Built-Up Area", 4: "Water Body"}
    tp = np.array([0, 10, 2, 5, 7])
    gt = np.array([0, 20, 4, 8, 10])
    pr = np.array([0, 15, 5, 9, 12])
    out = compute_counts_metrics(tp, gt, pr, class_names)
    assert "Bridge" in out
    assert out["Bridge"]["iou"] > 0


class DummyModel(torch.nn.Module):
    def __init__(self):
        super().__init__()

    def forward(self, x):
        # Predict class 1 for all pixels.
        b, _, h, w = x.shape
        y = torch.zeros((b, 5, h, w), device=x.device)
        y[:, 1] = 10.0
        return y


def test_evaluate_model_iou_runs():
    x = torch.randn(2, 3, 8, 8)
    y = torch.ones(2, 8, 8, dtype=torch.long)
    dl = DataLoader(TensorDataset(x, y), batch_size=1)
    device = torch.device("cpu")
    m = DummyModel().to(device)
    res = evaluate_model_iou(m, dl, device, 5)
    assert "mean_iou" in res
    assert res["iou_class_1"] > 0.99
