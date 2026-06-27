"""Generate architecture documentation from runtime configuration."""

from __future__ import annotations

from pathlib import Path

from src.config.platform_config import load_platform_config


def main() -> None:
    cfg = load_platform_config()
    out_path = Path("docs/ARCHITECTURE.generated.md")

    class_rows = "\n".join(
        f"| {c.id} | {c.name} | {list(c.color_rgb)} |" for c in cfg.classes
    )
    train_tiffs = "\n".join(f"- {name}" for name in cfg.train_tiffs)
    val_tiffs = "\n".join(f"- {name}" for name in cfg.val_tiffs)

    content = f"""# Generated Architecture Snapshot

Source of truth: config/platform_config.v1.json  
Version: {cfg.version}

## Classes
| ID | Name | Color RGB |
|---:|------|-----------|
{class_rows}

## Dataset Splits
### Train TIFFs
{train_tiffs}

### Validation TIFFs
{val_tiffs}

## Training Defaults
- architecture: {cfg.training.get('architecture')}
- encoder_name: {cfg.training.get('encoder_name')}
- image_size: {cfg.training.get('image_size')}
- patches_per_image: {cfg.training.get('patches_per_image')}
- batch_size: {cfg.training.get('batch_size')}
- accumulation_steps: {cfg.training.get('accumulation_steps')}
- num_epochs: {cfg.training.get('num_epochs')}

## Evaluation Defaults
- batch_size: {cfg.evaluation.get('batch_size')}
- num_workers: {cfg.evaluation.get('num_workers')}
- max_val_patches: {cfg.evaluation.get('max_val_patches')}

## System Diagram
```mermaid
flowchart TD
    A[Config JSON] --> B[Train Pipeline]
    A --> C[Unified Evaluator]
    A --> D[Inference Pipeline]
    C --> E[Evaluation Reports]
    D --> F[GeoTIFF Outputs]
```
"""
    out_path.write_text(content, encoding="utf-8")
    print(f"Generated {out_path}")


if __name__ == "__main__":
    main()
