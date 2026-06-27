"""Tests for model factory."""

from src.models.model_factory import create_model


def test_create_deeplabv3plus():
    model = create_model(
        architecture="DeepLabV3Plus",
        encoder_name="resnet50",
        encoder_weights=None,
        classes=5,
    )
    assert model is not None
