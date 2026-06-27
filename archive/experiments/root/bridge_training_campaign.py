"""Phase 4 bridge learning recovery training campaign."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch
from torch.amp import autocast

from src.config.platform_config import load_platform_config
from src.datasets.unified_dataset import CLASS_NAMES
from src.evaluation.unified_evaluator import compute_counts_metrics, create_shared_val_loader
from src.models.model_factory import create_model
from src.security.checkpoints import load_checkpoint_secure


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "outputs" / "bridge_campaign"
CURVES_DIR = OUT_DIR / "bridge_learning_curves"
BASELINE_CHECKPOINT = ROOT / "outputs" / "checkpoints" / "best_model.pth"


@dataclass
class ExperimentSpec:
    name: str
    label: str
    bridge_sampling_ratio: float
    class_balanced_sampling: bool
    hard_positive_mining: bool
    loss_name: str
    architecture: str = "DeepLabV3Plus"
    encoder_name: str = "resnet50"
    epochs: int = 4
    patches_per_image: int = 40
    early_bridge_zero_patience: int = 3
    use_init_checkpoint: bool = True


def ensure_dirs() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CURVES_DIR.mkdir(parents=True, exist_ok=True)


def run_cmd(cmd: list[str]) -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = "."
    subprocess.run(cmd, cwd=ROOT, env=env, check=True)


def experiment_paths(name: str) -> dict[str, Path]:
    exp_root = OUT_DIR / name
    return {
        "root": exp_root,
        "checkpoints": exp_root / "checkpoints",
        "history": exp_root / "training_history.json",
        "sampler": exp_root / "bridge_sampler_validation.md",
        "best": exp_root / "checkpoints" / "best_model.pth",
        "latest": exp_root / "checkpoints" / "latest_model.pth",
    }


def evaluate_checkpoint(checkpoint_path: Path) -> dict:
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    ckpt = load_checkpoint_secure(checkpoint_path, map_location=device)
    cfg = ckpt["config"]
    model = create_model(
        architecture=cfg.get("architecture", "DeepLabV3Plus"),
        encoder_name=cfg.get("encoder_name", "resnet50"),
        encoder_weights=None,
        in_channels=3,
        classes=cfg.get("classes", 5),
    )
    state_dict = ckpt.get("model_state_dict") or ckpt.get("ema_state_dict")
    model.load_state_dict(state_dict)
    model.to(device).eval()

    loader = create_shared_val_loader(cfg, batch_size=4, num_workers=0)
    num_classes = int(cfg.get("classes", 5))
    tp = np.zeros(num_classes, dtype=np.int64)
    gt_px = np.zeros(num_classes, dtype=np.int64)
    pr_px = np.zeros(num_classes, dtype=np.int64)

    t0 = time.time()
    with torch.no_grad():
        for images, masks in loader:
            images = images.to(device, non_blocking=True)
            masks = masks.to(device, non_blocking=True)
            with autocast(device_type="cuda", enabled=(device.type == "cuda")):
                logits = model(images)
            preds = logits.argmax(dim=1)

            preds_np = preds.cpu().numpy()
            masks_np = masks.cpu().numpy()
            for pred_mask, true_mask in zip(preds_np, masks_np):
                pred_flat = pred_mask.reshape(-1)
                true_flat = true_mask.reshape(-1)
                for class_id in range(num_classes):
                    tp[class_id] += int(((true_flat == class_id) & (pred_flat == class_id)).sum())
                    gt_px[class_id] += int((true_flat == class_id).sum())
                    pr_px[class_id] += int((pred_flat == class_id).sum())
    elapsed = time.time() - t0

    metrics = compute_counts_metrics(tp, gt_px, pr_px, CLASS_NAMES)
    metrics["eval_seconds"] = round(elapsed, 3)
    metrics["checkpoint_path"] = str(checkpoint_path)
    return metrics


def copy_baseline_checkpoint() -> dict:
    paths = experiment_paths("A_baseline")
    paths["checkpoints"].mkdir(parents=True, exist_ok=True)
    shutil.copy2(BASELINE_CHECKPOINT, paths["best"])
    shutil.copy2(BASELINE_CHECKPOINT, paths["latest"])
    metrics = evaluate_checkpoint(paths["best"])
    baseline_history = [
        {
            "epoch": 0,
            "bridge_iou": metrics["Bridge"]["iou"],
            "bridge_precision": metrics["Bridge"]["precision"],
            "bridge_recall": metrics["Bridge"]["recall"],
            "bridge_f1": metrics["Bridge"]["f1"],
            "val_iou": metrics["fg_miou"],
        }
    ]
    paths["history"].write_text(json.dumps(baseline_history, indent=2), encoding="utf-8")
    paths["sampler"].write_text(
        "# Bridge Sampler Validation\n\n- baseline checkpoint copied; no bridge-aware sampler active in baseline experiment\n",
        encoding="utf-8",
    )
    return {
        "name": "A_baseline",
        "label": "Baseline",
        "metrics": metrics,
        "history": baseline_history,
        "paths": {k: str(v) for k, v in paths.items()},
    }


def plot_learning_curves(name: str, history: list[dict]) -> dict:
    curve_dir = CURVES_DIR / name
    curve_dir.mkdir(parents=True, exist_ok=True)

    epochs = [int(h["epoch"]) for h in history]
    bridge_iou = [float(h.get("bridge_iou", 0.0)) for h in history]
    bridge_precision = [float(h.get("bridge_precision", 0.0)) for h in history]
    bridge_recall = [float(h.get("bridge_recall", 0.0)) for h in history]
    bridge_f1 = [float(h.get("bridge_f1", 0.0)) for h in history]

    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.plot(epochs, bridge_iou, label="Bridge IoU", color="#c0392b", linewidth=2)
    ax.plot(epochs, bridge_precision, label="Bridge Precision", color="#2980b9", linewidth=2)
    ax.plot(epochs, bridge_recall, label="Bridge Recall", color="#27ae60", linewidth=2)
    ax.plot(epochs, bridge_f1, label="Bridge F1", color="#8e44ad", linewidth=2)
    ax.set_xlabel("Epoch")
    ax.set_ylabel("Score")
    ax.set_ylim(0, 1.0)
    ax.grid(True, alpha=0.3)
    ax.legend()
    ax.set_title(f"{name} Bridge Learning Curves")
    fig.tight_layout()
    png_path = curve_dir / "bridge_learning_curve.png"
    fig.savefig(png_path, dpi=150)
    plt.close(fig)

    first_iou_epoch = next((ep for ep, value in zip(epochs, bridge_iou) if value > 0), None)
    first_f1_epoch = next((ep for ep, value in zip(epochs, bridge_f1) if value > 0), None)
    summary = {
        "curve_png": str(png_path),
        "first_bridge_iou_epoch": first_iou_epoch,
        "first_bridge_f1_epoch": first_f1_epoch,
        "peak_bridge_f1": max(bridge_f1) if bridge_f1 else 0.0,
    }
    (curve_dir / "curve_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def run_training_experiment(spec: ExperimentSpec) -> dict:
    paths = experiment_paths(spec.name)
    paths["checkpoints"].mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable,
        "train.py",
        "--experiment-name", spec.name,
        "--output-dir", str(paths["root"]),
        "--checkpoint-dir", str(paths["checkpoints"]),
        "--num-epochs", str(spec.epochs),
        "--patches-per-image", str(spec.patches_per_image),
        "--bridge-sampling-ratio", str(spec.bridge_sampling_ratio),
        "--selection-metric", "bridge_f1",
        "--early-bridge-zero-patience", str(spec.early_bridge_zero_patience),
        "--loss", spec.loss_name,
        "--architecture", spec.architecture,
        "--encoder-name", spec.encoder_name,
    ]
    if spec.use_init_checkpoint:
        cmd.extend(["--init-checkpoint", str(BASELINE_CHECKPOINT)])
    if spec.class_balanced_sampling:
        cmd.append("--class-balanced-sampling")
    if spec.hard_positive_mining:
        cmd.append("--hard-positive-mining")

    run_cmd(cmd)

    history = json.loads(paths["history"].read_text(encoding="utf-8"))
    curve_summary = plot_learning_curves(spec.name, history)
    metrics = evaluate_checkpoint(paths["best"])
    return {
        "name": spec.name,
        "label": spec.label,
        "spec": spec.__dict__,
        "metrics": metrics,
        "history": history,
        "curve_summary": curve_summary,
        "paths": {k: str(v) for k, v in paths.items()},
    }


def checkpoint_rank_key(result: dict) -> tuple:
    metrics = result["metrics"]
    bridge_f1 = float(metrics["Bridge"]["f1"])
    fg_miou = float(metrics["fg_miou"])
    road_iou = float(metrics["Road"]["iou"])
    built_iou = float(metrics["Built-Up Area"]["iou"])
    history = result.get("history", [])
    last_f1 = [float(h.get("bridge_f1", 0.0)) for h in history[-3:]]
    stability = 1.0 / (1.0 + float(np.std(last_f1))) if last_f1 else 0.0
    runtime = -float(metrics.get("eval_seconds", 0.0))
    return (bridge_f1, fg_miou, stability, road_iou, built_iou, runtime)


def write_sampler_validation(results: list[dict]) -> None:
    out = OUT_DIR / "bridge_sampler_validation.md"
    lines = ["# Bridge Sampler Validation", ""]
    for result in results:
        if result["name"] == "A_baseline":
            continue
        sampler_path = Path(result["paths"]["sampler"])
        lines.append(f"## {result['name']}")
        lines.append(sampler_path.read_text(encoding="utf-8").strip())
        lines.append("")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_campaign_report(results: list[dict]) -> None:
    out = OUT_DIR / "bridge_training_campaign.md"
    lines = ["# Bridge Training Campaign", "", "## Experiments"]
    for result in results:
        metrics = result["metrics"]
        lines.append(
            f"- {result['name']} ({result['label']}): Bridge IoU={metrics['Bridge']['iou']:.4f}, "
            f"Bridge F1={metrics['Bridge']['f1']:.4f}, Road IoU={metrics['Road']['iou']:.4f}, "
            f"Built-Up IoU={metrics['Built-Up Area']['iou']:.4f}, fg_mIoU={metrics['fg_miou']:.4f}, "
            f"checkpoint={result['paths']['best']}"
        )
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_checkpoint_comparison(results: list[dict]) -> list[dict]:
    ranked = sorted(results, key=checkpoint_rank_key, reverse=True)
    out = OUT_DIR / "checkpoint_comparison.md"
    lines = ["# Checkpoint Comparison", "", "## Ranking"]
    for idx, result in enumerate(ranked, start=1):
        metrics = result["metrics"]
        lines.append(
            f"{idx}. {result['name']}: Road IoU={metrics['Road']['iou']:.4f}, Bridge IoU={metrics['Bridge']['iou']:.4f}, "
            f"Bridge F1={metrics['Bridge']['f1']:.4f}, Built-Up IoU={metrics['Built-Up Area']['iou']:.4f}, "
            f"Water IoU={metrics['Water Body']['iou']:.4f}, fg_mIoU={metrics['fg_miou']:.4f}, eval_seconds={metrics.get('eval_seconds', 0.0):.3f}"
        )
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return ranked


def write_final_report(baseline: dict, ranked: list[dict]) -> None:
    best = ranked[0]
    base = baseline["metrics"]
    best_metrics = best["metrics"]

    def delta(class_name: str, key: str) -> float:
        return float(best_metrics[class_name][key]) - float(base[class_name][key])

    out = OUT_DIR / "final_bridge_recovery_report.md"
    lines = [
        "# Final Bridge Recovery Report",
        "",
        f"- Baseline checkpoint: {baseline['paths']['best']}",
        f"- Best model checkpoint: {best['paths']['best']}",
        f"- Best experiment: {best['name']}",
        "",
        "## Baseline",
        f"- Bridge IoU: {base['Bridge']['iou']:.4f}",
        f"- Bridge F1: {base['Bridge']['f1']:.4f}",
        f"- Road IoU: {base['Road']['iou']:.4f}",
        f"- Built-Up IoU: {base['Built-Up Area']['iou']:.4f}",
        f"- fg_mIoU: {base['fg_miou']:.4f}",
        "",
        "## Best Model",
        f"- Bridge IoU: {best_metrics['Bridge']['iou']:.4f}",
        f"- Bridge F1: {best_metrics['Bridge']['f1']:.4f}",
        f"- Road IoU: {best_metrics['Road']['iou']:.4f}",
        f"- Built-Up IoU: {best_metrics['Built-Up Area']['iou']:.4f}",
        f"- fg_mIoU: {best_metrics['fg_miou']:.4f}",
        "",
        "## Delta",
        f"- Bridge IoU Gain: {delta('Bridge', 'iou'):.4f}",
        f"- Bridge F1 Gain: {delta('Bridge', 'f1'):.4f}",
        f"- Road Impact: {delta('Road', 'iou'):.4f}",
        f"- Built-Up Impact: {delta('Built-Up Area', 'iou'):.4f}",
        f"- Overall mIoU Impact: {float(best_metrics['fg_miou']) - float(base['fg_miou']):.4f}",
    ]
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_segformer_report(result: dict) -> None:
    out = OUT_DIR / "segformer_bridge_report.md"
    metrics = result["metrics"]
    lines = [
        "# SegFormer Bridge Report",
        "",
        f"- Experiment: {result['name']}",
        f"- Bridge IoU: {metrics['Bridge']['iou']:.4f}",
        f"- Bridge F1: {metrics['Bridge']['f1']:.4f}",
        f"- Road IoU: {metrics['Road']['iou']:.4f}",
        f"- Built-Up IoU: {metrics['Built-Up Area']['iou']:.4f}",
        f"- fg_mIoU: {metrics['fg_miou']:.4f}",
    ]
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ensure_dirs()

    baseline = copy_baseline_checkpoint()

    experiments = [
        ExperimentSpec("B_bridge_sampler_only", "Bridge-aware sampler only", 0.25, False, False, "v2"),
        ExperimentSpec("C_bridge_sampler_class_balanced", "Bridge-aware sampler + class-balanced sampling", 0.25, True, False, "v2"),
        ExperimentSpec("D_bridge_sampler_hard_positive", "Bridge-aware sampler + hard positive mining", 0.25, False, True, "v2"),
        ExperimentSpec("E_bridge_sampler_focal_tversky", "Bridge-aware sampler + Focal Tversky", 0.25, False, False, "focal_tversky"),
        ExperimentSpec("F_bridge_sampler_hard_positive_focal_tversky", "Bridge-aware sampler + hard positive mining + Focal Tversky", 0.25, False, True, "focal_tversky"),
    ]

    results = [baseline]
    for spec in experiments:
        results.append(run_training_experiment(spec))

    best_parent = max(results[1:], key=lambda result: checkpoint_rank_key(result))
    best_spec = ExperimentSpec(
        name="G_best_configuration",
        label="Best configuration discovered so far",
        bridge_sampling_ratio=float(best_parent["spec"]["bridge_sampling_ratio"]),
        class_balanced_sampling=bool(best_parent["spec"]["class_balanced_sampling"]),
        hard_positive_mining=bool(best_parent["spec"]["hard_positive_mining"]),
        loss_name=str(best_parent["spec"]["loss_name"]),
        architecture=str(best_parent["spec"]["architecture"]),
        encoder_name=str(best_parent["spec"]["encoder_name"]),
        epochs=6,
        patches_per_image=60,
        early_bridge_zero_patience=4,
    )
    results.append(run_training_experiment(best_spec))

    deep_lab_results = [result for result in results if result["name"] != "A_baseline" and result["spec"]["architecture"] == "DeepLabV3Plus"]
    if all(float(result["metrics"]["Bridge"]["f1"]) <= 0.0 for result in deep_lab_results):
        segformer_spec = ExperimentSpec(
            name="SegFormer_B2_bridge_challenge",
            label="SegFormer-B2 bridge challenge",
            bridge_sampling_ratio=float(best_spec.bridge_sampling_ratio),
            class_balanced_sampling=bool(best_spec.class_balanced_sampling),
            hard_positive_mining=bool(best_spec.hard_positive_mining),
            loss_name=str(best_spec.loss_name),
            architecture="Segformer",
            encoder_name="mit_b2",
            epochs=4,
            patches_per_image=40,
            early_bridge_zero_patience=3,
            use_init_checkpoint=False,
        )
        try:
            segformer_result = run_training_experiment(segformer_spec)
            results.append(segformer_result)
            write_segformer_report(segformer_result)
        except subprocess.CalledProcessError as exc:
            (OUT_DIR / "segformer_bridge_report.md").write_text(
                "\n".join(
                    [
                        "# SegFormer Bridge Report",
                        "",
                        "- Status: failed",
                        f"- Command exited with code: {exc.returncode}",
                        "- Note: SegFormer branch failed but DeepLab campaign reports were still generated.",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

    write_sampler_validation(results)
    write_campaign_report(results)
    ranked = write_checkpoint_comparison(results)
    write_final_report(baseline, ranked)

    (OUT_DIR / "campaign_results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"Bridge training campaign artifacts written to {OUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())