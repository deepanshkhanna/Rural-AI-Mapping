"""Unified evaluation primitives used by all evaluation entry points."""

from __future__ import annotations

import numpy as np
import torch
from torch.amp import autocast
from torch.utils.data import DataLoader

from src.config.platform_config import load_platform_config
from src.datasets.unified_dataset import UnifiedMultiClassDataset, get_default_sources, get_val_transform


def create_shared_val_loader(model_cfg: dict, batch_size: int | None = None, num_workers: int | None = None) -> DataLoader:
    cfg = load_platform_config()
    bs = batch_size or int(cfg.evaluation.get("batch_size", 8))
    nw = num_workers if num_workers is not None else int(cfg.evaluation.get("num_workers", 4))
    image_size = model_cfg.get("image_size", cfg.training.get("image_size", 768))
    patches_per_image = model_cfg.get("patches_per_image", cfg.training.get("patches_per_image", 150))

    ds = UnifiedMultiClassDataset(
        sources=get_default_sources(),
        split="val",
        transform=get_val_transform(image_size),
        patch_size=image_size,
        patches_per_image=patches_per_image,
        train_tiffs=list(cfg.train_tiffs),
        val_tiffs=list(cfg.val_tiffs),
    )
    return DataLoader(ds, batch_size=bs, shuffle=False, num_workers=nw, pin_memory=True)


@torch.no_grad()
def evaluate_model_iou(model: torch.nn.Module, dataloader: DataLoader, device: torch.device, num_classes: int) -> dict[str, float]:
    total_intersection = torch.zeros(num_classes, device=device, dtype=torch.float64)
    total_union = torch.zeros(num_classes, device=device, dtype=torch.float64)

    for images, masks in dataloader:
        images = images.to(device, non_blocking=True)
        masks = masks.to(device, non_blocking=True)

        with autocast(device_type="cuda", enabled=(device.type == "cuda")):
            logits = model(images)
        preds = logits.argmax(dim=1)

        for c in range(num_classes):
            p = (preds == c).float()
            t = (masks == c).float()
            inter = (p * t).sum()
            total_intersection[c] += inter
            total_union[c] += p.sum() + t.sum() - inter

    smooth = 1e-6
    results: dict[str, float] = {}
    fg_ious: list[float] = []
    for c in range(1, num_classes):
        iou = (total_intersection[c] + smooth) / (total_union[c] + smooth)
        results[f"iou_class_{c}"] = iou.item()
        if total_union[c].item() > 0:
            fg_ious.append(iou.item())
    results["mean_iou"] = sum(fg_ious) / len(fg_ious) if fg_ious else 0.0
    return results


def compute_counts_metrics(tp: np.ndarray, gt_px: np.ndarray, pr_px: np.ndarray, class_names: dict[int, str]) -> dict:
    out: dict = {}
    fg_ious: list[float] = []
    for c in sorted(class_names.keys()):
        if c == 0:
            continue
        if gt_px[c] == 0:
            continue
        iou = float(tp[c]) / float(gt_px[c] + pr_px[c] - tp[c] + 1e-10)
        prec = float(tp[c]) / float(pr_px[c] + 1e-10)
        rec = float(tp[c]) / float(gt_px[c] + 1e-10)
        f1 = 2 * prec * rec / (prec + rec + 1e-10)
        out[class_names[c]] = {
            "iou": round(iou, 4),
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1": round(f1, 4),
            "gt_pixels": int(gt_px[c]),
        }
        fg_ious.append(iou)
    out["fg_miou"] = round(float(np.mean(fg_ious)) if fg_ious else 0.0, 4)
    return out
