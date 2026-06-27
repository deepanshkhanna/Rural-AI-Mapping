"""Evaluate SVAMITVA model on validation data with per-class IoU."""

import argparse
from pathlib import Path
import sys

import torch

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.datasets.unified_dataset import CLASS_NAMES
from src.evaluation.unified_evaluator import create_shared_val_loader, evaluate_model_iou
from src.models.model_factory import create_model
from src.security.checkpoints import load_checkpoint_secure


def load_model(checkpoint_path: str, device: torch.device) -> tuple:
    """Load trained model from checkpoint, return (model, config)."""
    checkpoint = load_checkpoint_secure(checkpoint_path, map_location=device)
    config = checkpoint.get("config", {})
    model = create_model(
        architecture=config.get("architecture", "DeepLabV3Plus"),
        encoder_name=config.get("encoder_name", "resnet50"),
        encoder_weights=None,
        in_channels=3,
        classes=config.get("classes", 4),
    )
    model.load_state_dict(checkpoint["model_state_dict"])
    model = model.to(device)
    model.eval()
    return model, config


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate SVAMITVA model")
    parser.add_argument("--checkpoint", type=str, default="outputs/checkpoints/best_model.pth")
    parser.add_argument("--batch-size", type=int, default=4)
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Loading model from {args.checkpoint}...")
    model, config = load_model(args.checkpoint, device)
    num_classes = config.get("classes", 4)

    print("Loading validation dataset...")
    dataloader = create_shared_val_loader(config, batch_size=args.batch_size)

    print(f"Evaluating on {len(dataloader.dataset)} patches...")
    metrics = evaluate_model_iou(model, dataloader, device, num_classes)

    print("\n" + "=" * 60)
    print("EVALUATION RESULTS")
    print("=" * 60)
    for c in range(1, num_classes):
        name = CLASS_NAMES.get(c, f"Class {c}")
        iou = metrics.get(f"iou_class_{c}", 0.0)
        print(f"  {name:14s}:  IoU={iou:.4f}")
    print(f"  {'Mean FG IoU':14s}:  {metrics['mean_iou']:.4f}")
    print("=" * 60)


if __name__ == "__main__":
    main()
