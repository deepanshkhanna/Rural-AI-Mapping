#!/usr/bin/env python3
"""Refresh PROJECT_BIBLE.md certified metrics from epoch_71_results.json."""

from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BIBLE = ROOT / "PROJECT_BIBLE.md"
METRICS = ROOT / "production_release/metrics/epoch_71_results.json"


def _load_metrics() -> dict:
    data = json.loads(METRICS.read_text())
    cal = data["eval_calibrated_tta"]["calibrated"]
    return {
        "fg_miou": cal["fg_miou"],
        "road": cal["Road"]["iou"],
        "built_up": cal["Built-Up Area"]["iou"],
        "water": cal["Water Body"]["iou"],
        "bridge": cal["Bridge"]["iou"],
        "val_patches": data.get("val_patches", 598),
        "best_epoch": data.get("best_epoch", 71),
        "latest_epoch": data.get("latest_epoch", 80),
    }


def _patch_table(text: str, m: dict) -> str:
    replacements = [
        (r"(\| FG mIoU \| )\*\*[\d.]+\*\*", rf"\g<1>**{m['fg_miou']:.4f}**"),
        (r"(\| Road IoU \| )[\d.]+", rf"\g<1>{m['road']:.4f}"),
        (r"(\| Built-Up IoU \| )[\d.]+", rf"\g<1>{m['built_up']:.4f}"),
        (r"(\| Water IoU \| )[\d.]+", rf"\g<1>{m['water']:.4f}"),
        (r"(\| Bridge IoU \| )[\d.]+", rf"\g<1>{m['bridge']:.1f}"),
        (r"(\| Val patches \| )\d+", rf"\g<1>{m['val_patches']}"),
    ]
    for pattern, repl in replacements:
        text = re.sub(pattern, repl, text)
    return text


def main() -> None:
    if not BIBLE.exists():
        raise SystemExit(f"Missing {BIBLE} — create base bible first.")
    if not METRICS.exists():
        raise SystemExit(f"Missing {METRICS}")

    m = _load_metrics()
    text = BIBLE.read_text()
    text = re.sub(
        r"\*\*Last updated:\*\* \d{4}-\d{2}-\d{2}",
        f"**Last updated:** {date.today().isoformat()}",
        text,
        count=1,
    )
    text = _patch_table(text, m)
    BIBLE.write_text(text)
    print(f"Updated {BIBLE} (FG mIoU {m['fg_miou']:.4f})")


if __name__ == "__main__":
    main()
