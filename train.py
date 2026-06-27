"""Main training script for SVAMITVA multi-class feature extraction."""

import argparse
import copy
import json
import os
import random
import sys
import time
from pathlib import Path

import numpy as np
import torch
from torch.amp import GradScaler
from torch.utils.data import DataLoader

sys.path.insert(0, str(Path(__file__).parent))

from src.datasets.unified_dataset import (
    UnifiedMultiClassDataset,
    get_default_sources,
    get_train_transform,
    get_val_transform,
)
from src.config.platform_config import load_platform_config
from src.data_validation.validator import DatasetValidator
from src.losses.multiclass_loss import FocalTverskyLoss, MultiClassCompositeLoss, MultiClassCompositeLossV2
from src.models.model_factory import create_model
from src.security.checkpoints import load_checkpoint_secure
from src.training.train_one_epoch import train_one_epoch, validate_multiclass


PLATFORM_CFG = load_platform_config()

# ── TIFF-level train / val split (single source of truth) ─────────────────
TRAIN_TIFFS = list(PLATFORM_CFG.train_tiffs)
VAL_TIFFS = list(PLATFORM_CFG.val_tiffs)

# Training configuration
CONFIG = {
    # Data
    "image_size": int(PLATFORM_CFG.training.get("image_size", 768)),
    "patches_per_image": int(PLATFORM_CFG.training.get("patches_per_image", 150)),

    # Training
    "batch_size": int(PLATFORM_CFG.training.get("batch_size", 4)),
    "num_epochs": int(PLATFORM_CFG.training.get("num_epochs", 80)),
    "learning_rate": 1e-4,
    "encoder_lr": 1e-5,
    "weight_decay": 1e-4,
    "max_grad_norm": 1.0,
    "accumulation_steps": 8,    # effective batch 32 (was 16) — halves gradient variance

    # Model
    "architecture": str(PLATFORM_CFG.training.get("architecture", "DeepLabV3Plus")),
    "encoder_name": str(PLATFORM_CFG.training.get("encoder_name", "resnet50")),
    "encoder_weights": str(PLATFORM_CFG.training.get("encoder_weights", "imagenet")),
    "classes": PLATFORM_CFG.num_classes,  # single source of truth
    "seed": 42,
    "use_gradient_checkpointing": True,

    # Validation enhancements (TTA disabled during training — too slow)
    "use_multiscale_val": True,
    "use_road_refinement": True,
    "use_tta": False,           # disabled: saves 57% val time per epoch

    # Loss  (V2: OHEM-CE + label-smoothed conditional Dice)
    "ce_weight": 0.5,       # ohem_weight in V2
    "dice_weight": 0.5,     # dice_weight in V2
    "label_eps": 0.05,      # label smoothing — prevents logit over-confidence
    "bridge_min_pixels": 100,  # skip bridge Dice when batch has <100 bridge GT px

    # LR warmup
    "warmup_epochs": 5,     # linear warmup before scheduler takes over

    # EMA
    "ema_decay": 0.99,      # ~100 steps window (~2.6 epochs) — meaningful by epoch 5

    # Scheduler
    "scheduler_type": "plateau",

    # DataLoader
    "num_workers": min(4, os.cpu_count() or 4),
    "persistent_workers": True,
    "prefetch_factor": 2,

    # Bridge recovery training knobs
    "bridge_sampling_ratio": 0.0,
    "class_balanced_sampling": False,
    "hard_positive_mining": False,
    "bridge_catalog_path": "outputs/bridge_phase3/bridge_patch_catalog/metadata.json",
    "selection_metric": "val_iou",
    "early_bridge_zero_patience": 0,
    "experiment_name": "default",
    "loss_name": "v2",

    # Output
    "output_dir": "outputs",
    "checkpoint_dir": "outputs/checkpoints",

    # Resume
    "resume_checkpoint": None,
}


# ── EMA (Exponential Moving Average) ──────────────────────────────────────

class EMA:
    """Exponential Moving Average of model parameters.

    Maintains a shadow copy of the model weights that smoothly tracks the
    training weights.  Eliminates epoch-to-epoch variance and prevents
    catastrophic forgetting on minority classes (Built-Up collapse fix).
    """

    def __init__(self, model: torch.nn.Module, decay: float = 0.999) -> None:
        self.decay = decay
        self.shadow = copy.deepcopy(model.state_dict())
        self.backup: dict | None = None

    @torch.no_grad()
    def update(self, model: torch.nn.Module) -> None:
        # Use named_parameters/buffers to avoid state_dict() copy overhead on every step
        for name, param in model.named_parameters():
            self.shadow[name].mul_(self.decay).add_(param.data, alpha=1.0 - self.decay)
        for name, buf in model.named_buffers():
            self.shadow[name].copy_(buf)

    def apply_shadow(self, model: torch.nn.Module) -> None:
        """Swap model weights with EMA weights (for validation)."""
        self.backup = copy.deepcopy(model.state_dict())
        model.load_state_dict(self.shadow)

    def restore(self, model: torch.nn.Module) -> None:
        """Restore original model weights after validation."""
        if self.backup is not None:
            model.load_state_dict(self.backup)
            self.backup = None

    def state_dict(self) -> dict:
        return self.shadow


# ── Helpers ────────────────────────────────────────────────────────────────

def set_seed(seed: int = 42) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


def _worker_init_fn(worker_id: int) -> None:
    base_seed = torch.initial_seed() % 2**32
    np.random.seed(base_seed + worker_id)
    random.seed(base_seed + worker_id)


def setup_cuda_optimizations() -> None:
    if torch.cuda.is_available():
        torch.backends.cuda.matmul.allow_tf32 = True
        torch.backends.cudnn.allow_tf32 = True


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train SVAMITVA multi-class model")
    parser.add_argument("--experiment-name", type=str, default=CONFIG["experiment_name"])
    parser.add_argument("--output-dir", type=str, default=CONFIG["output_dir"])
    parser.add_argument("--checkpoint-dir", type=str, default=CONFIG["checkpoint_dir"])
    parser.add_argument("--num-epochs", type=int, default=CONFIG["num_epochs"])
    parser.add_argument("--patches-per-image", type=int, default=CONFIG["patches_per_image"])
    parser.add_argument("--batch-size", type=int, default=CONFIG["batch_size"])
    parser.add_argument("--learning-rate", type=float, default=CONFIG["learning_rate"])
    parser.add_argument("--encoder-lr", type=float, default=CONFIG["encoder_lr"])
    parser.add_argument("--image-size", type=int, default=CONFIG["image_size"])
    parser.add_argument("--architecture", type=str, default=CONFIG["architecture"])
    parser.add_argument("--encoder-name", type=str, default=CONFIG["encoder_name"])
    parser.add_argument("--resume-checkpoint", type=str, default=None)
    parser.add_argument("--init-checkpoint", type=str, default=None)
    parser.add_argument("--bridge-sampling-ratio", type=float, default=CONFIG["bridge_sampling_ratio"])
    parser.add_argument("--class-balanced-sampling", action="store_true")
    parser.add_argument("--hard-positive-mining", action="store_true")
    parser.add_argument("--bridge-catalog-path", type=str, default=CONFIG["bridge_catalog_path"])
    parser.add_argument("--selection-metric", choices=["val_iou", "bridge_f1"], default=CONFIG["selection_metric"])
    parser.add_argument("--early-bridge-zero-patience", type=int, default=CONFIG["early_bridge_zero_patience"])
    parser.add_argument("--loss", choices=["v2", "focal_tversky"], default=CONFIG["loss_name"])
    parser.add_argument("--dry-run-loader", action="store_true")
    parser.add_argument("--dry-run-batches", type=int, default=12)
    parser.add_argument("--skip-validation", action="store_true", help="Skip dataset preflight validation")
    return parser.parse_args()


def build_config(args: argparse.Namespace) -> dict:
    config = copy.deepcopy(CONFIG)
    config.update(
        {
            "experiment_name": args.experiment_name,
            "output_dir": args.output_dir,
            "checkpoint_dir": args.checkpoint_dir,
            "num_epochs": args.num_epochs,
            "patches_per_image": args.patches_per_image,
            "batch_size": args.batch_size,
            "learning_rate": args.learning_rate,
            "encoder_lr": args.encoder_lr,
            "image_size": args.image_size,
            "architecture": args.architecture,
            "encoder_name": args.encoder_name,
            "resume_checkpoint": args.resume_checkpoint,
            "init_checkpoint": args.init_checkpoint,
            "bridge_sampling_ratio": args.bridge_sampling_ratio,
            "class_balanced_sampling": args.class_balanced_sampling,
            "hard_positive_mining": args.hard_positive_mining,
            "bridge_catalog_path": args.bridge_catalog_path,
            "selection_metric": args.selection_metric,
            "early_bridge_zero_patience": args.early_bridge_zero_patience,
            "loss_name": args.loss,
        }
    )
    return config


def collect_loader_bridge_stats(dataloader: DataLoader, max_batches: int) -> dict[str, float | int]:
    bridge_patch_count = 0
    bridge_pixel_count = 0
    bridge_batch_count = 0
    total_patches = 0

    for batch_idx, (_images, masks) in enumerate(dataloader):
        bridge_pixels_batch = int((masks == 2).sum().item())
        bridge_samples_batch = int(((masks == 2).view(masks.shape[0], -1).sum(dim=1) > 0).sum().item())
        bridge_patch_count += bridge_samples_batch
        bridge_pixel_count += bridge_pixels_batch
        if bridge_pixels_batch > 0:
            bridge_batch_count += 1
        total_patches += int(masks.shape[0])
        if batch_idx + 1 >= max_batches:
            break

    observed_batches = min(len(dataloader), max_batches)
    return {
        "observed_batches": observed_batches,
        "observed_patches": total_patches,
        "bridge_patch_count": bridge_patch_count,
        "bridge_pixel_count": bridge_pixel_count,
        "bridge_batch_frequency": bridge_batch_count / max(observed_batches, 1),
        "bridge_patch_frequency": bridge_patch_count / max(total_patches, 1),
    }


def write_bridge_sampler_validation(report_path: Path, dataset, observed: dict | None = None, history: list[dict] | None = None) -> None:
    summary = dataset.sampling_summary() if hasattr(dataset, "sampling_summary") else {}
    lines = [
        "# Bridge Sampler Validation",
        "",
        f"- bridge sampling ratio: {summary.get('bridge_sampling_ratio', 0.0):.4f}",
        f"- bridge stride: {summary.get('bridge_stride', 0)}",
        f"- expected bridge samples/epoch: {summary.get('expected_bridge_samples_per_epoch', 0)}",
        f"- bridge TIFF count: {summary.get('bridge_tiffs', 0)}",
        f"- hard positive catalog patches: {summary.get('hard_positive_catalog_patches', 0)}",
        f"- class balanced sampling: {summary.get('class_balanced_sampling', False)}",
        f"- hard positive mining: {summary.get('hard_positive_mining', False)}",
    ]
    if observed:
        lines.extend(
            [
                "",
                "## Observed Loader Stats",
                f"- observed batches: {observed.get('observed_batches', 0)}",
                f"- observed patches: {observed.get('observed_patches', 0)}",
                f"- bridge patch count: {observed.get('bridge_patch_count', 0)}",
                f"- bridge pixel count: {observed.get('bridge_pixel_count', 0)}",
                f"- bridge batch frequency: {observed.get('bridge_batch_frequency', 0.0):.4f}",
                f"- bridge patch frequency: {observed.get('bridge_patch_frequency', 0.0):.4f}",
            ]
        )
    if history:
        lines.extend(["", "## Epoch Bridge Tracking"])
        for record in history:
            lines.append(
                f"- epoch {record['epoch']}: train_bridge_patches={record.get('train_bridge_patch_count', 0)}, "
                f"train_bridge_pixels={record.get('train_bridge_pixel_count', 0)}, "
                f"train_bridge_batch_frequency={record.get('train_bridge_batch_frequency', 0.0):.4f}, "
                f"bridge_iou={record.get('bridge_iou', 0.0):.4f}, bridge_f1={record.get('bridge_f1', 0.0):.4f}"
            )
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def create_dataloaders(config: dict) -> tuple[DataLoader, DataLoader]:
    """Create train and val dataloaders with TIFF-level split."""
    train_dataset = UnifiedMultiClassDataset(
        sources=get_default_sources(),
        split="train",
        transform=get_train_transform(config["image_size"]),
        patch_size=config["image_size"],
        patches_per_image=config.get("patches_per_image", 100),
        positive_sampling_prob=0.9,    # ↑ from 0.7 — forces more retries for positive patches
        bridge_sampling_ratio=config.get("bridge_sampling_ratio", 0.0),
        class_balanced_sampling=config.get("class_balanced_sampling", False),
        hard_positive_mining=config.get("hard_positive_mining", False),
        bridge_catalog_path=config.get("bridge_catalog_path"),
        train_tiffs=TRAIN_TIFFS,
        val_tiffs=VAL_TIFFS,
    )

    val_dataset = UnifiedMultiClassDataset(
        sources=get_default_sources(),
        split="val",
        transform=get_val_transform(config["image_size"]),
        patch_size=config["image_size"],
        patches_per_image=config.get("patches_per_image", 100),
        train_tiffs=TRAIN_TIFFS,
        val_tiffs=VAL_TIFFS,
    )

    nw = config["num_workers"]
    pw = config["persistent_workers"] if nw > 0 else False
    pf = config["prefetch_factor"] if nw > 0 else None

    train_loader = DataLoader(
        train_dataset,
        batch_size=config["batch_size"],
        shuffle=True,
        num_workers=nw,
        pin_memory=True,
        persistent_workers=pw,
        prefetch_factor=pf,
        drop_last=True,
        worker_init_fn=_worker_init_fn,
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size=config["batch_size"],
        shuffle=False,
        num_workers=nw,
        pin_memory=True,
        persistent_workers=pw,
        prefetch_factor=pf,
        worker_init_fn=_worker_init_fn,
    )

    return train_loader, val_loader


# ── Main ───────────────────────────────────────────────────────────────────

def main() -> None:
    args = parse_args()
    config = build_config(args)

    set_seed(config["seed"])
    setup_cuda_optimizations()
    Path(config["output_dir"]).mkdir(parents=True, exist_ok=True)
    Path(config["checkpoint_dir"]).mkdir(parents=True, exist_ok=True)

    if not args.skip_validation:
        val_report = DatasetValidator().run()
        if not val_report.ok:
            print(f"Dataset validation failed ({len(val_report.issues)} issues). Use --skip-validation to override.")
            for issue in val_report.issues[:10]:
                print(f"  [{issue.severity}] {issue.asset}: {issue.message}")
            raise SystemExit(2)

    if config["batch_size"] < 2:
        raise ValueError("batch_size must be >= 2 (BatchNorm constraint)")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    print("=" * 80)
    print("TRAINING CONFIGURATION  —  SVAMITVA Multi-Class Pipeline")
    print("=" * 80)
    print(f"Device:        {device}")
    if torch.cuda.is_available():
        print(f"GPU:           {torch.cuda.get_device_name(0)}")
        print(f"CUDA:          {torch.version.cuda}")
    print(f"Dataset:       Unified PB + CG ({len(TRAIN_TIFFS)} train, {len(VAL_TIFFS)} val TIFFs)")
    print(f"Classes:       {config['classes']}  "
          "(0=BG, 1=Road, 2=Bridge, 3=Built-Up Area, 4=Water Body)")
    print(f"Reproducibility active: seed={config['seed']}")
    print(f"Model:         {config['architecture']} ({config['encoder_name']} backbone)")
    print(f"Image size:    {config['image_size']}")
    print(f"Batch size:    {config['batch_size']}  (effective {config['batch_size'] * config['accumulation_steps']})")
    print(f"Epochs:        {config['num_epochs']}")
    print(f"Experiment:    {config['experiment_name']}")
    print(f"EMA decay:     {config['ema_decay']}")
    print(f"Bridge ratio:  {config.get('bridge_sampling_ratio', 0.0):.2f}")
    print(f"Class balance: {config.get('class_balanced_sampling', False)}")
    print(f"Hard positive: {config.get('hard_positive_mining', False)}")
    if config.get("use_road_refinement"):
        print("Road structural refinement: ENABLED")
    if config.get("use_multiscale_val"):
        print("Multi-scale validation: ENABLED")
    print(f"TTA during training: {'ENABLED' if config.get('use_tta') else 'DISABLED (fast val)'}")
    if config.get("loss_name") == "focal_tversky":
        print("Loss:          Focal Tversky")
    else:
        print(f"Loss:          V2 — OHEM({config['ce_weight']}) + SmoothedDice({config['dice_weight']})  "
              f"label_eps={config.get('label_eps', 0.05)}")
    print(f"Warmup:        {config.get('warmup_epochs', 0)} epochs linear LR warmup")
    print(f"Scheduler:     ReduceLROnPlateau patience=10 (was 5)")
    print("=" * 80)

    # Create dataloaders
    print("\nCreating SVAMITVA dataloaders...")
    train_loader, val_loader = create_dataloaders(config)
    print(f"Train batches: {len(train_loader)}")
    print(f"Val batches:   {len(val_loader)}")

    sampler_report_path = Path(config["output_dir"]) / "bridge_sampler_validation.md"
    observed_loader_stats = collect_loader_bridge_stats(train_loader, max_batches=args.dry_run_batches)
    write_bridge_sampler_validation(sampler_report_path, train_loader.dataset, observed=observed_loader_stats)
    print(f"Bridge sampler validation written to: {sampler_report_path}")
    if args.dry_run_loader:
        print(json.dumps(observed_loader_stats, indent=2))
        return

    # Create model
    print("\nCreating model...")
    model = create_model(
        architecture=config["architecture"],
        encoder_name=config["encoder_name"],
        encoder_weights=config["encoder_weights"],
        in_channels=3,
        classes=config["classes"],
        use_gradient_checkpointing=config["use_gradient_checkpointing"],
    )
    model = model.to(device)

    # EMA
    ema = EMA(model, decay=config["ema_decay"])
    print(f"  EMA tracking: ENABLED (decay={config['ema_decay']})")

    # Loss — V2: OHEM-CE + label-smoothed conditional Dice
    if config.get("loss_name") == "focal_tversky":
        criterion = FocalTverskyLoss(num_classes=config["classes"])
    else:
        criterion = MultiClassCompositeLossV2(
            num_classes=config["classes"],
            ohem_weight=config["ce_weight"],
            dice_weight=config["dice_weight"],
            label_eps=config.get("label_eps", 0.05),
            bridge_min_pixels=config.get("bridge_min_pixels", 100),
        )

    # Optimizer with differential learning rates
    encoder_params = []
    decoder_params = []
    for name, param in model.named_parameters():
        if "encoder" in name:
            encoder_params.append(param)
        else:
            decoder_params.append(param)

    optimizer = torch.optim.AdamW(
        [
            {"params": encoder_params, "lr": config["encoder_lr"]},
            {"params": decoder_params, "lr": config["learning_rate"]},
        ],
        weight_decay=config["weight_decay"],
    )

    # Store initial LR for warmup scheduling
    for group in optimizer.param_groups:
        group["initial_lr"] = group["lr"]

    # Scheduler
    scheduler_type = config.get("scheduler_type", "plateau")
    if scheduler_type == "cosine":
        scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
            optimizer, T_max=config["num_epochs"], eta_min=1e-6,
        )
    else:
        scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
            optimizer, mode="max", factor=0.5, patience=10,
            threshold=1e-4, min_lr=1e-6,
        )

    scaler = GradScaler("cuda")

    print(f"Initial LR (encoder): {optimizer.param_groups[0]['lr']}")
    print(f"Initial LR (decoder): {optimizer.param_groups[1]['lr']}")
    print(f"Scheduler: {type(scheduler).__name__}")

    # Resume from checkpoint if specified
    start_epoch = 1
    best_score = float("-inf")
    training_history: list[dict] = []
    history_path = Path(config["output_dir"]) / "training_history.json"
    zero_bridge_streak = 0

    resume_path = config.get("resume_checkpoint")
    if resume_path and Path(resume_path).exists():
        print(f"\nResuming from checkpoint: {resume_path}")
        ckpt = load_checkpoint_secure(resume_path, map_location=device)
        model.load_state_dict(ckpt["model_state_dict"])
        optimizer.load_state_dict(ckpt["optimizer_state_dict"])
        scheduler.load_state_dict(ckpt["scheduler_state_dict"])
        scaler.load_state_dict(ckpt["scaler_state_dict"])
        start_epoch = ckpt["epoch"] + 1
        best_score = ckpt.get("best_score", ckpt.get("best_iou", 0.0))
        if "ema_state_dict" in ckpt:
            ema.shadow = ckpt["ema_state_dict"]
        if history_path.exists():
            with open(history_path) as f:
                training_history = json.load(f)
        print(f"Resumed at epoch {start_epoch}, best_score={best_score:.4f}")
    else:
        init_path = config.get("init_checkpoint")
        if init_path and Path(init_path).exists():
            print(f"\nInitializing model weights from checkpoint: {init_path}")
            ckpt = load_checkpoint_secure(init_path, map_location=device)
            init_state = ckpt.get("ema_state_dict") or ckpt.get("model_state_dict")
            model.load_state_dict(init_state)
            ema.shadow = copy.deepcopy(init_state)
            print("Loaded model/EMA weights for warm-start fine-tuning")

    # Training loop
    print("\n" + "=" * 80)
    print("STARTING TRAINING")
    print("=" * 80)

    epoch_times = []

    for epoch in range(start_epoch, config["num_epochs"] + 1):
        epoch_start = time.time()

        print(f"\n{'─' * 80}")
        print(f"Epoch {epoch}/{config['num_epochs']}")
        print(f"{'─' * 80}")

        # Train (EMA updated per-step inside train_one_epoch)
        train_metrics = train_one_epoch(
            model=model,
            dataloader=train_loader,
            criterion=criterion,
            optimizer=optimizer,
            scaler=scaler,
            device=device,
            max_grad_norm=config["max_grad_norm"],
            accumulation_steps=config["accumulation_steps"],
            ema=ema,
        )

        # Validate using actual model weights (clean signal for LR scheduler)
        # EMA weights are used only for saving the best checkpoint
        val_metrics = validate_multiclass(
            model=model,
            dataloader=val_loader,
            criterion=criterion,
            device=device,
            num_classes=config["classes"],
            use_multiscale=config.get("use_multiscale_val", False),
            use_road_refinement=config.get("use_road_refinement", False),
            use_tta=config.get("use_tta", False),
        )

        # Update scheduler — warmup phase overrides LR directly for first N epochs
        warmup_epochs = config.get("warmup_epochs", 0)
        if warmup_epochs > 0 and epoch <= warmup_epochs:
            factor = epoch / warmup_epochs
            for group in optimizer.param_groups:
                group["lr"] = group["initial_lr"] * factor
        elif isinstance(scheduler, torch.optim.lr_scheduler.ReduceLROnPlateau):
            scheduler.step(val_metrics["val_iou"])
        else:
            scheduler.step()

        # GPU memory
        if torch.cuda.is_available():
            mem_allocated = torch.cuda.memory_allocated(0) / 1024**3
            mem_reserved = torch.cuda.memory_reserved(0) / 1024**3
        else:
            mem_allocated = mem_reserved = 0.0

        # ETA
        epoch_elapsed = time.time() - epoch_start
        epoch_times.append(epoch_elapsed)
        avg_epoch_time = sum(epoch_times) / len(epoch_times)
        remaining_epochs = config["num_epochs"] - epoch
        eta_seconds = int(avg_epoch_time * remaining_epochs)
        h, m, s = eta_seconds // 3600, (eta_seconds % 3600) // 60, eta_seconds % 60
        eta_str = f"{h:02d}:{m:02d}:{s:02d}"

        # Persist epoch metrics
        epoch_record = {
            "epoch":         epoch,
            "train_loss":    train_metrics["train_loss"],
            "train_time":    train_metrics["train_time"],
            "train_bridge_patch_count": int(train_metrics.get("bridge_patch_count", 0)),
            "train_bridge_pixel_count": int(train_metrics.get("bridge_pixel_count", 0)),
            "train_bridge_batch_frequency": train_metrics.get("bridge_batch_frequency", 0.0),
            "val_loss":      val_metrics["val_loss"],
            "val_iou":       val_metrics["val_iou"],
            "val_dice":      val_metrics["val_dice"],
            "per_class_iou": {str(k): v for k, v in val_metrics.get("per_class_iou", {}).items()},
            "per_class_dice":{str(k): v for k, v in val_metrics.get("per_class_dice", {}).items()},
            "per_class_precision": {str(k): v for k, v in val_metrics.get("per_class_precision", {}).items()},
            "per_class_recall": {str(k): v for k, v in val_metrics.get("per_class_recall", {}).items()},
            "per_class_f1": {str(k): v for k, v in val_metrics.get("per_class_f1", {}).items()},
            "bridge_iou": val_metrics.get("per_class_iou", {}).get(2, 0.0),
            "bridge_precision": val_metrics.get("per_class_precision", {}).get(2, 0.0),
            "bridge_recall": val_metrics.get("per_class_recall", {}).get(2, 0.0),
            "bridge_f1": val_metrics.get("per_class_f1", {}).get(2, 0.0),
            "lr_encoder":    optimizer.param_groups[0]["lr"],
            "lr_decoder":    optimizer.param_groups[1]["lr"],
            "epoch_time":    epoch_elapsed,
        }
        training_history.append(epoch_record)
        with open(history_path, "w") as f:
            json.dump(training_history, f, indent=2)
        write_bridge_sampler_validation(sampler_report_path, train_loader.dataset, observed=observed_loader_stats, history=training_history)

        # Print metrics
        print(f"\nTrain Loss:  {train_metrics['train_loss']:.4f}")
        print(f"Val Loss:    {val_metrics['val_loss']:.4f}")
        print(f"Val mIoU:    {val_metrics['val_iou']:.4f}  (best checkpoint: EMA)")
        print(f"Val mDice:   {val_metrics['val_dice']:.4f}")
        print(
            f"Bridge Val:  IoU={epoch_record['bridge_iou']:.4f}  P={epoch_record['bridge_precision']:.4f}  "
            f"R={epoch_record['bridge_recall']:.4f}  F1={epoch_record['bridge_f1']:.4f}"
        )
        print(
            f"Bridge Train: patches={epoch_record['train_bridge_patch_count']}  pixels={epoch_record['train_bridge_pixel_count']}  "
            f"batch_freq={epoch_record['train_bridge_batch_frequency']:.4f}"
        )
        print(f"Epoch Time:  {epoch_elapsed:.1f}s (train={train_metrics['train_time']:.1f}s)")
        print(f"GPU Memory:  {mem_allocated:.2f}GB / {mem_reserved:.2f}GB")
        print(f"LR enc/dec:  {optimizer.param_groups[0]['lr']:.2e} / {optimizer.param_groups[1]['lr']:.2e}")
        print(f"ETA:         {eta_str}")

        current_score = epoch_record["bridge_f1"] if config.get("selection_metric") == "bridge_f1" else val_metrics["val_iou"]

        # Save best model (EMA weights)
        if current_score > best_score:
            best_score = current_score
            checkpoint_path = Path(config["checkpoint_dir"]) / "best_model.pth"
            torch.save(
                {
                    "epoch": epoch,
                    "model_state_dict": ema.state_dict(),
                    "optimizer_state_dict": optimizer.state_dict(),
                    "scheduler_state_dict": scheduler.state_dict(),
                    "scaler_state_dict": scaler.state_dict(),
                    "ema_state_dict": ema.state_dict(),
                    "best_iou": val_metrics["val_iou"],
                    "best_score": best_score,
                    "config": config,
                    "metrics": {**train_metrics, **val_metrics},
                },
                checkpoint_path,
            )
            print(f"\n✓ Saved best EMA model ({config.get('selection_metric')}: {best_score:.4f})")

        # Save latest checkpoint (training weights + EMA)
        checkpoint_path = Path(config["checkpoint_dir"]) / "latest_model.pth"
        torch.save(
            {
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "scheduler_state_dict": scheduler.state_dict(),
                "scaler_state_dict": scaler.state_dict(),
                "ema_state_dict": ema.state_dict(),
                "best_iou": val_metrics["val_iou"],
                "best_score": best_score,
                "config": config,
                "metrics": {**train_metrics, **val_metrics},
            },
            checkpoint_path,
        )

        if epoch_record["bridge_f1"] <= 1e-9:
            zero_bridge_streak += 1
        else:
            zero_bridge_streak = 0

        patience = int(config.get("early_bridge_zero_patience", 0))
        if patience > 0 and zero_bridge_streak >= patience:
            print(f"\n[EARLY STOP] Bridge F1 remained zero for {zero_bridge_streak} epoch(s)")
            break

    print("\n" + "=" * 80)
    print("TRAINING COMPLETE")
    print("=" * 80)
    print(f"Best selection score: {best_score:.4f}")
    print(f"Checkpoints saved to: {config['checkpoint_dir']}")
    print(f"Training history:     {history_path}")
    print("=" * 80 + "\n")

    # Generate training visualizations
    print("Generating training plots...")
    try:
        from visualize_training import main as visualize
        visualize(history_path)
    except Exception as exc:
        print(f"[WARN] Visualization failed: {exc}")


if __name__ == "__main__":
    main()
