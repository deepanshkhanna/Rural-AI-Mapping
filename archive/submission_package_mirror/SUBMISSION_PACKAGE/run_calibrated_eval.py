"""
Calibrated Pipeline Evaluation — measures improvement over raw baseline.

Runs baseline (no postprocess) and calibrated pipeline on the validation set
from a single execution. Writes provenance-stamped results JSON.

Usage:
    python run_calibrated_eval.py
    python run_calibrated_eval.py --require-bias   # fail if optimal_bias.json missing
"""

from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import DataLoader
from tqdm import tqdm

from src.config.platform_config import load_platform_config
from src.data_validation.validator import DatasetValidator
from src.datasets.unified_dataset import (
    CLASS_NAMES,
    get_default_sources,
    UnifiedMultiClassDataset,
    get_val_transform,
)
from src.evaluation.unified_evaluator import compute_counts_metrics
from src.inference.calibrated_engine import CalibratedEngine
from src.logging_config import configure_logging, get_logger
from src.security.checkpoints import load_checkpoint_secure

configure_logging()
LOGGER = get_logger(__name__)

PLATFORM_CFG = load_platform_config()
NUM_CLASSES = PLATFORM_CFG.num_classes
VAL_TIFFS = list(PLATFORM_CFG.val_tiffs)
TRAIN_TIFFS = list(PLATFORM_CFG.train_tiffs)
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


def _git_sha() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return "unknown"


def run_eval(engine: CalibratedEngine, val_loader: DataLoader, postprocess: bool) -> dict:
    tp = np.zeros(NUM_CLASSES, dtype=np.int64)
    gt_px = np.zeros(NUM_CLASSES, dtype=np.int64)
    pr_px = np.zeros(NUM_CLASSES, dtype=np.int64)

    for images, masks in tqdm(val_loader, desc=f"Eval (postproc={postprocess})"):
        preds_np, _ = engine.predict_batch(
            images,
            postprocess=postprocess,
            strict_postprocess=postprocess,
        )
        masks_np = masks.numpy()
        for b in range(preds_np.shape[0]):
            p = preds_np[b].flatten()
            t = masks_np[b].flatten()
            for c in range(NUM_CLASSES):
                tp[c] += ((t == c) & (p == c)).sum()
                gt_px[c] += (t == c).sum()
                pr_px[c] += (p == c).sum()

    return compute_counts_metrics(tp, gt_px, pr_px, CLASS_NAMES)


def _print_results(title: str, results: dict) -> None:
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print(f"{'=' * 70}")
    print(f"  FG mIoU:  {results['fg_miou']:.4f}")
    print(f"  {'Class':20s} {'IoU':>8s} {'Prec':>8s} {'Recall':>8s} {'F1':>8s}")
    print(f"  {'-' * 64}")
    for name, m in results.items():
        if name == "fg_miou":
            continue
        print(
            f"  {name:20s} {m['iou']:8.4f} {m['precision']:8.4f} "
            f"{m['recall']:8.4f} {m['f1']:8.4f}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Calibrated pipeline evaluation")
    parser.add_argument(
        "--require-bias",
        action="store_true",
        help="Fail if outputs/optimal_bias.json is missing",
    )
    parser.add_argument(
        "--skip-validation",
        action="store_true",
        help="Skip dataset preflight validation",
    )
    args = parser.parse_args()

    best_ckpt = Path("outputs/checkpoints/best_model.pth")
    latest_ckpt = Path("outputs/checkpoints/latest_model.pth")
    bias_path = Path("outputs/optimal_bias.json")

    if not best_ckpt.exists() or not latest_ckpt.exists():
        LOGGER.error("Missing checkpoints: %s, %s", best_ckpt, latest_ckpt)
        LOGGER.error("Run: python scripts/build_synthetic_fixtures.py (CI) or scripts/fetch_artifacts.sh")
        return 1

    if not args.skip_validation:
        report = DatasetValidator().run()
        if not report.ok:
            LOGGER.error("Dataset validation failed (%d issues)", len(report.issues))
            for issue in report.issues[:10]:
                LOGGER.error("[%s] %s — %s", issue.severity, issue.asset, issue.message)
            return 2

    print("=" * 70)
    print("  CALIBRATED PIPELINE EVALUATION")
    print("  Ensemble + OptimalBias + RoadGapFill + BridgeRecovery")
    print("=" * 70)

    LOGGER.info("Loading calibrated engine...")
    engine = CalibratedEngine.from_checkpoints(
        best_ckpt,
        latest_ckpt,
        device=DEVICE,
        bias_path=bias_path,
        use_tta=True,
        require_bias_file=args.require_bias,
    )

    ckpt = load_checkpoint_secure(best_ckpt, map_location="cpu")
    cfg = ckpt["config"]
    image_size = cfg.get("image_size", 768)

    LOGGER.info("Creating val loader...")
    val_ds = UnifiedMultiClassDataset(
        sources=get_default_sources(),
        split="val",
        transform=get_val_transform(image_size),
        patch_size=image_size,
        patches_per_image=cfg.get("patches_per_image", 50),
        train_tiffs=TRAIN_TIFFS,
        val_tiffs=VAL_TIFFS,
    )
    val_loader = DataLoader(
        val_ds,
        batch_size=int(PLATFORM_CFG.evaluation.get("batch_size", 8)),
        shuffle=False,
        num_workers=int(PLATFORM_CFG.evaluation.get("num_workers", 4)),
        pin_memory=True,
    )
    LOGGER.info("Validation patches: %d", len(val_ds))

    t0 = time.time()
    baseline_results = run_eval(engine, val_loader, postprocess=False)
    calibrated_results = run_eval(engine, val_loader, postprocess=True)
    elapsed = time.time() - t0

    _print_results("BASELINE (no postprocess)", baseline_results)
    _print_results("CALIBRATED PIPELINE", calibrated_results)

    print(f"\n  Delta (calibrated - baseline) FG mIoU: "
          f"{calibrated_results['fg_miou'] - baseline_results['fg_miou']:+.4f}")
    print(f"  Total eval time: {elapsed:.1f}s")

    provenance = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S %z"),
        "git_sha": _git_sha(),
        "python": platform.python_version(),
        "torch": torch.__version__,
        "device": DEVICE,
        "val_tiffs": VAL_TIFFS,
        "patch_size": image_size,
        "val_patches": len(val_ds),
        "calibration": engine.provenance(),
        "eval_seconds": round(elapsed, 2),
    }

    output = {
        "provenance": provenance,
        "baseline": baseline_results,
        "calibrated": calibrated_results,
    }

    out_path = Path("outputs/calibrated_eval_results.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)
    LOGGER.info("Saved results to %s", out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
