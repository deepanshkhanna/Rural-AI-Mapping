"""Tests for loss functions."""

import torch

from src.losses.multiclass_loss import MultiClassCompositeLossV2, OHEMLoss


def test_ohem_loss_finite():
    loss_fn = OHEMLoss(top_ratio=0.3)
    logits = torch.randn(2, 5, 32, 32)
    targets = torch.randint(0, 5, (2, 32, 32))
    loss = loss_fn(logits, targets)
    assert torch.isfinite(loss)


def test_composite_v2_backward():
    loss_fn = MultiClassCompositeLossV2(num_classes=5)
    logits = torch.randn(1, 5, 16, 16, requires_grad=True)
    targets = torch.randint(0, 5, (1, 16, 16))
    loss = loss_fn(logits, targets)
    loss.backward()
    assert logits.grad is not None
