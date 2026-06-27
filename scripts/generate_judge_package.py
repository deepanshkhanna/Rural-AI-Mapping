#!/usr/bin/env python3
"""
Generate a self-contained judge evidence package.

Outputs:
  evidence/judge_package/
    index.html              — visual report (open in browser)
    survey_intelligence.json
    verification_manifest.json
    overlays/               — PNG evidence images
    metrics.json            — GT vs prediction IoU on synthetic ortho

Usage:
    python scripts/generate_judge_package.py
    python scripts/generate_judge_package.py --train  # train demo model first
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import subprocess
import sys
from io import BytesIO
from pathlib import Path

import numpy as np
import rasterio
from rasterio.windows import Window
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ.setdefault("SVAMITVA_CONFIG_PATH", "config/platform_config.synthetic.json")

from src.config.platform_config import load_platform_config
from src.datasets.unified_dataset import UnifiedMultiClassDataset, get_default_sources, get_val_transform
from src.evaluation.unified_evaluator import compute_counts_metrics
from src.inference.calibrated_engine import CalibratedEngine, pixel_size_from_transform
from src.intelligence.survey_report import build_survey_intelligence
from src.intelligence.survey_operations import render_field_verification_overlay

OUT = ROOT / "evidence" / "judge_package"
OVERLAYS = OUT / "overlays"

CLASS_COLORS = np.array([
    [0, 0, 0], [255, 0, 0], [0, 0, 255], [255, 255, 0], [0, 200, 255],
], dtype=np.uint8)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()


def _git_sha() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True, cwd=ROOT).strip()
    except Exception:
        return "unknown"


def _colorize(mask: np.ndarray) -> np.ndarray:
    return CLASS_COLORS[mask]


def _overlay(rgb: np.ndarray, mask: np.ndarray, alpha: float = 0.45) -> np.ndarray:
    base = rgb.astype(np.float32) / 255.0
    col = _colorize(mask).astype(np.float32) / 255.0
    a = np.where(mask[..., None] > 0, alpha, 0.0)
    return np.clip((1 - a) * base + a * col, 0, 1)


def _save_png(arr: np.ndarray, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if arr.dtype != np.uint8:
        arr = (np.clip(arr, 0, 1) * 255).astype(np.uint8)
    Image.fromarray(arr).save(path)


def _b64_img(path: Path) -> str:
    data = path.read_bytes()
    return base64.b64encode(data).decode("ascii")


def _compute_gt_pred_metrics(pred: np.ndarray, gt: np.ndarray, class_names: dict) -> dict:
    num_classes = len(class_names)
    tp = np.zeros(num_classes, dtype=np.int64)
    gt_px = np.zeros(num_classes, dtype=np.int64)
    pr_px = np.zeros(num_classes, dtype=np.int64)
    for c in range(num_classes):
        tp[c] = ((pred == c) & (gt == c)).sum()
        gt_px[c] = (gt == c).sum()
        pr_px[c] = (pred == c).sum()
    return compute_counts_metrics(tp, gt_px, pr_px, class_names)


def _rasterize_gt_full(tiff_path: Path) -> tuple[np.ndarray, np.ndarray]:
    """Build GT mask aligned to full TIFF using dataset loader logic."""
    cfg = load_platform_config()
    ds = UnifiedMultiClassDataset(
        sources=get_default_sources(),
        split="val",
        transform=None,
        patch_size=256,
        patches_per_image=1,
        train_tiffs=list(cfg.train_tiffs),
        val_tiffs=list(cfg.val_tiffs),
    )
    entry = ds.entries[0]
    with rasterio.open(tiff_path) as src:
        h, w = src.height, src.width
        win = Window(0, 0, w, h)
        rgb = src.read([1, 2, 3]).transpose(1, 2, 0).astype(np.uint8)
        gt = ds._rasterize_patch(win, src.transform, entry.layers, h)
    return rgb, gt


def _rasterize_gt_patch(tiff_path: Path, image_size: int) -> tuple[np.ndarray, np.ndarray]:
    """Top-left verification window (legacy, for overlay thumbnails)."""
    with rasterio.open(tiff_path) as src:
        ps = min(image_size, src.height, src.width)
        win = Window(0, 0, ps, ps)
        rgb = src.read([1, 2, 3], window=win).transpose(1, 2, 0).astype(np.uint8)
    cfg = load_platform_config()
    ds = UnifiedMultiClassDataset(
        sources=get_default_sources(),
        split="val",
        transform=None,
        patch_size=image_size,
        patches_per_image=1,
        train_tiffs=list(cfg.train_tiffs),
        val_tiffs=list(cfg.val_tiffs),
    )
    entry = ds.entries[0]
    with rasterio.open(tiff_path) as src:
        win = Window(0, 0, ps, ps)
        gt = ds._rasterize_patch(win, src.transform, entry.layers, ps)
    return rgb, gt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--train", action="store_true", help="Run synthetic demo training first")
    args = parser.parse_args()

    if args.train:
        subprocess.check_call([sys.executable, str(ROOT / "scripts" / "build_synthetic_fixtures.py"), "--skip-checkpoints"])
        subprocess.check_call([sys.executable, str(ROOT / "scripts" / "train_synthetic_demo.py")])
    else:
        ckpt = ROOT / "outputs/checkpoints/best_model.pth"
        flags = ["--skip-checkpoints"] if ckpt.exists() else []
        subprocess.check_call([sys.executable, str(ROOT / "scripts" / "build_synthetic_fixtures.py"), *flags])

    subprocess.check_call(["bash", str(ROOT / "scripts" / "reproduce.sh")])

    tiff_path = ROOT / "tests/fixtures/synthetic/tiffs/SYNTHETIC_TEST_ORTHO.tif"
    if not tiff_path.exists():
        print(f"Missing synthetic TIFF: {tiff_path}")
        return 1

    cfg = load_platform_config()
    class_names = cfg.class_names

    device = "cuda" if __import__("torch").cuda.is_available() else "cpu"
    engine = CalibratedEngine.from_checkpoints(
        ROOT / "outputs/checkpoints/best_model.pth",
        ROOT / "outputs/checkpoints/latest_model.pth",
        device=device,
        bias_path=ROOT / "outputs/optimal_bias.json",
        use_tta=False,
    )

    rgb_full, gt_full = _rasterize_gt_full(tiff_path)

    pred_full, logits = engine.predict_large(
        rgb_full, patch_size=engine.image_size, overlap=64, postprocess=False
    )

    # Scoring uses full raster (all labeled classes present); overlays use center patch.
    metrics = _compute_gt_pred_metrics(pred_full, gt_full, class_names)

    center = engine.image_size
    y0 = max(0, (rgb_full.shape[0] - center) // 2)
    x0 = max(0, (rgb_full.shape[1] - center) // 2)
    rgb_patch = rgb_full[y0 : y0 + center, x0 : x0 + center]
    gt_patch = gt_full[y0 : y0 + center, x0 : x0 + center]
    pred_patch = pred_full[y0 : y0 + center, x0 : x0 + center]

    # Visual evidence
    OVERLAYS.mkdir(parents=True, exist_ok=True)
    _save_png(rgb_patch, OVERLAYS / "01_input_rgb.png")
    _save_png(_colorize(gt_patch), OVERLAYS / "02_ground_truth.png")
    _save_png(_colorize(pred_patch), OVERLAYS / "03_prediction.png")
    _save_png(_overlay(rgb_patch, pred_patch), OVERLAYS / "04_overlay.png")

    conf = np.exp(logits - logits.max(axis=0, keepdims=True))
    conf = conf / (conf.sum(axis=0, keepdims=True) + 1e-9)
    conf_map = conf.max(axis=0)[y0 : y0 + center, x0 : x0 + center]
    conf_rgb = _confidence_heatmap(conf_map)
    _save_png(conf_rgb, OVERLAYS / "05_confidence.png")

    # Error map: white=correct foreground, red=FP, blue=FN
    err = np.zeros((*gt_patch.shape, 3), dtype=np.uint8)
    for c in range(1, 5):
        gt_c = gt_patch == c
        pr_c = pred_patch == c
        err[gt_c & pr_c] = [0, 200, 0]
        err[pr_c & ~gt_c] = [255, 80, 80]
        err[gt_c & ~pr_c] = [80, 80, 255]
    _save_png(err, OVERLAYS / "06_error_map.png")

    eval_path = ROOT / "outputs/calibrated_eval_results.json"
    eval_data = json.loads(eval_path.read_text()) if eval_path.exists() else {}

    with rasterio.open(tiff_path) as src:
        gsd = pixel_size_from_transform(src.transform)

    provenance = {
        "git_sha": _git_sha(),
        "tiff": str(tiff_path.relative_to(ROOT)),
        "tiff_sha256": _sha256(tiff_path),
        "best_ckpt_sha256": _sha256(ROOT / "outputs/checkpoints/best_model.pth"),
        "eval_artifact": str(eval_path.relative_to(ROOT)) if eval_path.exists() else None,
        "gsd_m": gsd,
        "verification_window_px": list(gt_patch.shape),
        "scoring_scope": "full_raster",
    }

    survey = build_survey_intelligence(
        pred_full,
        pixel_size_m=gsd,
        village_name="Synthetic Verification Village",
        logits=logits,
        provenance=provenance,
    )
    survey.save_json(OUT / "survey_intelligence.json")

    queue = survey.field_verification.get("field_verification_queue", [])
    priority_overlay = render_field_verification_overlay(rgb_full, queue)
    _save_png(priority_overlay, OVERLAYS / "07_field_priority_map.png")

    package_metrics = {
        "patch_verification": metrics,
        "scoring_scope": "full_raster",
        "overlay_window": "center_patch",
        "full_raster_shape": list(pred_full.shape),
        "eval_pipeline": eval_data,
    }
    (OUT / "metrics.json").write_text(json.dumps(package_metrics, indent=2), encoding="utf-8")

    # Manifest
    manifest_files = []
    for p in sorted(OUT.rglob("*")):
        if p.is_file():
            manifest_files.append({
                "path": str(p.relative_to(OUT)),
                "sha256": _sha256(p),
                "bytes": p.stat().st_size,
            })
    manifest = {
        "package_version": "1.0",
        "provenance": provenance,
        "files": manifest_files,
        "reproduce_commands": [
            "bash scripts/reproduce.sh",
            "python scripts/generate_judge_package.py --train",
        ],
    }
    (OUT / "verification_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    _write_html(OUT / "index.html", metrics, survey.to_dict(), provenance, eval_data)
    print(f"Judge package written to {OUT}")
    print(f"Open: file://{OUT / 'index.html'}")
    return 0


def _confidence_heatmap(conf: np.ndarray) -> np.ndarray:
    """Simple red-yellow-green confidence heatmap without matplotlib."""
    c = np.clip(conf, 0, 1)
    rgb = np.zeros((*c.shape, 3), dtype=np.uint8)
    rgb[..., 0] = ((1 - c) * 255).astype(np.uint8)
    rgb[..., 1] = (c * 200).astype(np.uint8)
    rgb[..., 2] = (c * 80).astype(np.uint8)
    return rgb


def _write_html(path: Path, metrics: dict, survey: dict, provenance: dict, eval_data: dict) -> None:
    imgs = {
        "input": _b64_img(OVERLAYS / "01_input_rgb.png"),
        "gt": _b64_img(OVERLAYS / "02_ground_truth.png"),
        "pred": _b64_img(OVERLAYS / "03_prediction.png"),
        "overlay": _b64_img(OVERLAYS / "04_overlay.png"),
        "conf": _b64_img(OVERLAYS / "05_confidence.png"),
        "error": _b64_img(OVERLAYS / "06_error_map.png"),
    }
    priority_path = OVERLAYS / "07_field_priority_map.png"
    if priority_path.exists():
        imgs["priority"] = _b64_img(priority_path)

    metric_rows = ""
    for name, m in metrics.items():
        if name == "fg_miou":
            continue
        metric_rows += (
            f"<tr><td>{name}</td><td>{m['iou']:.4f}</td><td>{m['precision']:.4f}</td>"
            f"<td>{m['recall']:.4f}</td><td>{m['gt_pixels']}</td></tr>"
        )

    fv = survey.get("field_verification", {})
    accessibility = fv.get("village_accessibility_score", 0)
    queue = fv.get("field_verification_queue", [])
    top_priorities = fv.get("top_field_priorities", [])

    queue_rows = ""
    for item in queue[:5]:
        bd = item.get("score_breakdown", {})
        queue_rows += f"""<tr>
<td><strong>{item.get('rank')}</strong></td>
<td>{item.get('score', 0):.1f}</td>
<td>{item.get('label', '')}</td>
<td>{item.get('access_assessment', '')}</td>
<td>{item.get('mean_confidence', 0):.2f}</td>
<td style="font-size:0.9rem">{item.get('reason', '')}</td>
</tr>"""

    breakdown_sample = ""
    if queue:
        bd = queue[0].get("score_breakdown", {})
        breakdown_sample = (
            f"Score breakdown (rank 1): confidence risk {bd.get('confidence_risk', 0):.0f}, "
            f"isolation {bd.get('isolation_risk', 0):.0f}, size {bd.get('cluster_size', 0):.0f}, "
            f"water prox {bd.get('water_proximity', 0):.0f}, fragmentation {bd.get('fragmentation_context', 0):.0f}"
        )

    priority_lines = "".join(f"<li>{p}</li>" for p in top_priorities[:3])
    exec_rest = "".join(
        f"<li>{line}</li>" for line in survey.get("executive_summary", [])[4:]
    )

    priority_img_html = ""
    if "priority" in imgs:
        priority_img_html = f"""
<div class="card primary">
<h2>If your team visits only three places tomorrow</h2>
<img src="data:image/png;base64,{imgs['priority']}" alt="field priority map" style="width:100%;max-width:900px;border-radius:8px;border:1px solid #30363d"/>
<p class="warn">Numbered markers: 1 = highest priority field verification target.</p>
</div>"""

    html = f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"/>
<title>SVAMITVA Field Verification — Judge Evidence</title>
<style>
body{{font-family:system-ui,sans-serif;max-width:1100px;margin:2rem auto;padding:0 1rem;background:#0d1117;color:#e6edf3}}
h1{{color:#58a6ff}} h2{{color:#79c0ff;border-bottom:1px solid #30363d;padding-bottom:.3rem}}
.card{{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:1rem;margin:1rem 0}}
.card.primary{{border-color:#58a6ff;border-width:2px}}
.grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:.5rem}}
.grid img{{width:100%;border-radius:4px;border:1px solid #30363d}}
table{{width:100%;border-collapse:collapse}} td,th{{border:1px solid #30363d;padding:.4rem;text-align:left}}
code{{background:#21262d;padding:.1rem .3rem;border-radius:3px}}
.warn{{color:#ffb86c}}
.lead{{font-size:1.1rem;line-height:1.5;color:#c9d1d9}}
.score{{font-size:2rem;font-weight:800;color:#58a6ff}}
</style></head><body>
<h1>SVAMITVA Field Verification Priorities</h1>
<p class="lead">Operational decision support for district survey officers — <strong>where to send your field team first</strong>,
derived deterministically from segmentation + confidence (no black box).</p>

<div class="card primary">
<h2>Field Verification Priorities</h2>
<p>Village Accessibility Score: <span class="score">{accessibility:.0f}/100</span></p>
<h3>Top 3 visits tomorrow</h3>
<ul>{priority_lines}</ul>
<h3>Ranked queue</h3>
<table>
<tr><th>#</th><th>Score</th><th>Target</th><th>Access</th><th>Confidence</th><th>Reason</th></tr>
{queue_rows if queue_rows else '<tr><td colspan="6">No high-priority targets — spot-check low-confidence pixels</td></tr>'}
</table>
<p style="font-size:0.85rem;color:#8b949e">{breakdown_sample}</p>
</div>

{priority_img_html}

<div class="card">
<h2>Survey Context</h2>
<ul>{exec_rest}</ul>
</div>

<div class="card">
<h2>Visual Evidence (center patch)</h2>
<div class="grid">
<figure><img src="data:image/png;base64,{imgs['input']}" alt="input"/><figcaption>Input RGB</figcaption></figure>
<figure><img src="data:image/png;base64,{imgs['gt']}" alt="gt"/><figcaption>Ground Truth</figcaption></figure>
<figure><img src="data:image/png;base64,{imgs['pred']}" alt="pred"/><figcaption>Prediction</figcaption></figure>
<figure><img src="data:image/png;base64,{imgs['overlay']}" alt="overlay"/><figcaption>Overlay</figcaption></figure>
<figure><img src="data:image/png;base64,{imgs['conf']}" alt="conf"/><figcaption>Confidence</figcaption></figure>
<figure><img src="data:image/png;base64,{imgs['error']}" alt="error"/><figcaption>Error Map</figcaption></figure>
</div>
</div>

<div class="card">
<h2>Pipeline Verification Metrics <span class="warn">(synthetic benchmark only)</span></h2>
<p>FG mIoU: <strong>{metrics.get('fg_miou', 0):.4f}</strong> — pipeline integrity check, not production claim.</p>
<table><tr><th>Class</th><th>IoU</th><th>Precision</th><th>Recall</th><th>GT px</th></tr>{metric_rows}</table>
</div>

<div class="card">
<h2>Provenance</h2>
<ul>
<li>Git SHA: <code>{provenance.get('git_sha','?')}</code></li>
<li>TIFF SHA-256: <code>{provenance.get('tiff_sha256','?')[:16]}…</code></li>
<li>Checkpoint SHA-256: <code>{provenance.get('best_ckpt_sha256','?')[:16]}…</code></li>
<li>GSD: {provenance.get('gsd_m')} m/px</li>
</ul>
</div>

<div class="card">
<h2>Pipeline Eval Artifact</h2>
<pre>{json.dumps(eval_data.get('provenance', {}), indent=2)[:2000]}</pre>
</div>
</body></html>"""
    path.write_text(html, encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
