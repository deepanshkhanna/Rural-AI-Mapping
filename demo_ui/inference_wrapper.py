"""
inference_wrapper.py — Demo UI inference bridge.

Delegates to CalibratedEngine.predict_large for sliding-window orthomosaic inference.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import numpy as np

from src.inference.calibrated_engine import CalibratedEngine
from src.inference.tiling import count_tiles
from src.postprocessing import classify_rooftops, get_infrastructure_summary

ROOT = Path(__file__).parent.parent
BEST_CKPT = ROOT / "outputs" / "checkpoints" / "best_model.pth"
LATEST_CKPT = ROOT / "outputs" / "checkpoints" / "latest_model.pth"
BIAS_JSON = ROOT / "outputs" / "optimal_bias.json"

CLASS_NAMES = {
    0: "Background",
    1: "Road",
    2: "Bridge",
    3: "Built-Up Area",
    4: "Water Body",
}

CLASS_COLORS = np.array([
    [0, 0, 0],
    [255, 0, 0],
    [0, 0, 255],
    [255, 255, 0],
    [0, 200, 255],
], dtype=np.uint8)

ROOFTOP_COLOR = np.array([255, 140, 0], dtype=np.uint8)

_engine: CalibratedEngine | None = None


def reset_engine() -> None:
    global _engine
    _engine = None


def _get_engine() -> CalibratedEngine:
    global _engine
    if _engine is None:
        import torch

        device = "cuda" if torch.cuda.is_available() else "cpu"
        _engine = CalibratedEngine.from_checkpoints(
            BEST_CKPT,
            LATEST_CKPT,
            device=device,
            bias_path=BIAS_JSON,
            use_tta=True,
        )
    return _engine


def predict_image(
    image_rgb: np.ndarray,
    use_tta: bool = True,
    return_confidence: bool = False,
):
    engine = _get_engine()
    engine.use_tta = use_tta
    mask, logit_acc = engine.predict_large(
        image_rgb,
        patch_size=engine.image_size,
        overlap=max(32, engine.image_size // 6),
        postprocess=True,
    )
    if return_confidence:
        exp_logits = np.exp(logit_acc - logit_acc.max(axis=0, keepdims=True))
        probs = exp_logits / (exp_logits.sum(axis=0, keepdims=True) + 1e-9)
        conf_map = probs.max(axis=0).astype(np.float32)
        return mask, conf_map
    return mask


def load_tiff_rgb_preview(tiff_path: Path, max_dim: int = 2048) -> np.ndarray:
    """Load RGB from GeoTIFF for UI preview (optionally downscaled)."""
    import rasterio
    from PIL import Image

    with rasterio.open(tiff_path) as src:
        data = src.read(indexes=[1, 2, 3])
        rgb = np.transpose(data, (1, 2, 0)).astype(np.uint8)
    h, w = rgb.shape[:2]
    if max(h, w) > max_dim:
        scale = max_dim / max(h, w)
        nh, nw = int(h * scale), int(w * scale)
        rgb = np.array(Image.fromarray(rgb).resize((nw, nh), Image.LANCZOS))
    return rgb


def estimate_tiff_inference(
    tiff_path: Path,
    use_tta: bool = True,
) -> dict:
    """Estimate tile count and wall-clock seconds for demo UI ETA."""
    import rasterio

    engine = _get_engine()
    patch_size = engine.image_size
    overlap = max(32, patch_size // 6)
    with rasterio.open(tiff_path) as src:
        h, w = src.height, src.width
    tiles = count_tiles(h, w, patch_size, overlap)
    sec_per_batch = 1.8 if engine.device == "cuda" else 7.0
    if use_tta:
        sec_per_batch *= 3.0
    batches = max(1, (tiles + 3) // 4)
    main_sec = batches * sec_per_batch
    megapixels = (h * w) / 1_000_000
    finalize_sec = max(8.0, megapixels * 0.8)
    confidence_sec = 12.0 if use_tta else 6.0
    return {
        "tiles": tiles,
        "batches": batches,
        "device": engine.device,
        "estimated_seconds": int(main_sec + finalize_sec + confidence_sec),
        "width": w,
        "height": h,
    }


def predict_tiff_file(
    tiff_path: Path,
    use_tta: bool = True,
    return_confidence: bool = False,
    return_meta: bool = False,
    progress_callback: Callable[[float, str], None] | None = None,
):
    """Full-resolution inference on an official demo GeoTIFF (windowed read, no full-RGB load)."""
    engine = _get_engine()
    engine.use_tta = use_tta
    estimate = estimate_tiff_inference(tiff_path, use_tta=use_tta)

    def _report(fraction: float, message: str) -> None:
        if progress_callback is not None:
            progress_callback(min(max(fraction, 0.0), 1.0), message)

    _report(0.0, f"Starting inference — ~{estimate['tiles']} tiles on {estimate['device']}")

    def _engine_progress(fraction: float, message: str) -> None:
        _report(0.05 + 0.85 * min(max(fraction, 0.0), 1.0), message)

    mask, meta = engine.predict_tiff(
        tiff_path,
        output_path=None,
        postprocess=True,
        progress_callback=_engine_progress,
    )

    if not return_confidence:
        _report(1.0, "Done")
        if return_meta:
            return mask, meta
        return mask

    _report(0.88, "Building confidence map (preview)…")
    preview = load_tiff_rgb_preview(tiff_path, max_dim=1024)
    engine.use_tta = False  # preview only — never 3× full pass after GeoTIFF
    _, conf_map = predict_image(preview, use_tta=False, return_confidence=True)
    engine.use_tta = use_tta
    _report(1.0, "Done")
    if return_meta:
        return mask, conf_map, meta
    return mask, conf_map


def colorize_mask(mask: np.ndarray) -> np.ndarray:
    return CLASS_COLORS[mask]


def colorize_with_rooftops(mask: np.ndarray, rooftop_mask=None) -> np.ndarray:
    rgb = CLASS_COLORS[mask].copy()
    if rooftop_mask is not None and rooftop_mask.any():
        rgb[rooftop_mask] = ROOFTOP_COLOR
    return rgb


def colorize_confidence(conf_map: np.ndarray) -> np.ndarray:
    import matplotlib.cm as cm

    cmap = cm.get_cmap("RdYlGn")
    rgba = cmap(conf_map)
    return (rgba[:, :, :3] * 255).astype(np.uint8)


def create_overlay(image_rgb, mask, alpha=0.45, rooftop_mask=None):
    if image_rgb.shape[2] == 4:
        image_rgb = image_rgb[:, :, :3]
    img_f = image_rgb.astype(np.float32) / 255.0
    msk_f = colorize_with_rooftops(mask, rooftop_mask).astype(np.float32) / 255.0
    a = np.where(mask[..., None] > 0, alpha, 0.0)
    return np.clip((1 - a) * img_f + a * msk_f, 0, 1)


def get_class_stats(mask, rooftop_mask=None):
    total = mask.size
    stats = {
        CLASS_NAMES[i]: {
            "pixels": int((mask == i).sum()),
            "pct": float(100.0 * (mask == i).sum() / total),
            "color": CLASS_COLORS[i].tolist(),
        }
        for i in range(len(CLASS_NAMES))
    }
    if rooftop_mask is not None:
        rooftop_px = int(rooftop_mask.sum())
        stats["Rooftop (est.)"] = {
            "pixels": rooftop_px,
            "pct": float(100.0 * rooftop_px / total),
            "color": ROOFTOP_COLOR.tolist(),
        }
    return stats


def model_info() -> dict:
    engine = _get_engine()
    prov = engine.provenance()
    return {
        "checkpoint": BEST_CKPT.name,
        "epoch": prov.get("best_ckpt", "?"),
        "best_miou": 0.0,
        "device": engine.device,
        "classes": list(CLASS_NAMES.values()),
        "ensemble": True,
        "bias_tuned": BIAS_JSON.exists(),
        "pipeline": "CalibratedEngine.predict_tiff / predict_large (ensemble + bias + TTA + postprocess)",
        "patch_size": engine.image_size,
    }


__all__ = [
    "CLASS_NAMES",
    "CLASS_COLORS",
    "ROOFTOP_COLOR",
    "classify_rooftops",
    "colorize_mask",
    "colorize_with_rooftops",
    "colorize_confidence",
    "create_overlay",
    "get_class_stats",
    "get_infrastructure_summary",
    "load_tiff_rgb_preview",
    "estimate_tiff_inference",
    "model_info",
    "predict_image",
    "predict_tiff_file",
]
