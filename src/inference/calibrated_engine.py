"""
Calibrated Inference Engine — production pipeline.

Combines:
  1. Two-model EMA ensemble (best + latest), weighted 65/35
  2. Per-class logit bias (tuned by bias_search.py)
  3. TTA: horizontal + vertical flip averaging
  4. Enhanced postprocessing (road gap fill, bridge spatial recovery)
  5. Village-level quantitative statistics

Usage:
    from src.inference.calibrated_engine import CalibratedEngine
    engine = CalibratedEngine.from_checkpoints(
        best_ckpt, latest_ckpt, device, bias_path="outputs/optimal_bias.json"
    )
    pred_mask, stats = engine.predict_patch(image_tensor)
    pred_mask, stats = engine.predict_tiff(tiff_path, output_path)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Callable, Optional, Union

import numpy as np
import rasterio
import torch
import torch.nn.functional as F
from rasterio.windows import Window

from src.config.platform_config import load_platform_config
from src.inference.tiling import (
    accumulate_logits,
    finalize_logits,
    iter_tiles,
    normalize_patch_rgb,
)
from src.logging_config import get_logger
from src.models.model_factory import create_model
from src.postprocessing import (
    bridge_recovery_from_builtup,
    classify_rooftops,
    get_infrastructure_summary,
    postprocess_mask,
    road_gap_fill,
)
from src.security.checkpoints import file_sha256, load_checkpoint_secure

LOGGER = get_logger(__name__)

CLASS_NAMES = {0: "Background", 1: "Road", 2: "Bridge", 3: "Built-Up Area", 4: "Water Body"}
NUM_CLASSES = 5

_DEFAULT_BIAS = [0.0, 1.5, 4.0, 0.0, 0.0]
_IMAGENET_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
_IMAGENET_STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)


def pixel_size_from_transform(transform) -> float:
    """Return absolute ground sample distance (m) from an affine transform."""
    return float(abs(transform.a))


class CalibratedEngine:
    """Two-model ensemble inference + calibrated decision + enhanced postprocessing."""

    def __init__(
        self,
        model_best: torch.nn.Module,
        model_latest: torch.nn.Module,
        device: str,
        image_size: int = 768,
        bias: list | None = None,
        w_best: float = 0.65,
        w_latest: float = 0.35,
        use_tta: bool = True,
        bias_path: Path | None = None,
        require_bias_file: bool = False,
    ):
        self.model_best = model_best
        self.model_latest = model_latest
        self.device = device
        self.image_size = image_size
        self.w_best = w_best
        self.w_latest = w_latest
        self.use_tta = use_tta
        self.bias_path = bias_path
        self.bias_source = "default"

        b = bias if bias is not None else _DEFAULT_BIAS
        self.bias = torch.tensor(b, dtype=torch.float32, device=device).view(1, NUM_CLASSES, 1, 1)

        if require_bias_file and (bias_path is None or not Path(bias_path).exists()):
            raise FileNotFoundError(
                f"Bias file required for scoring mode but missing: {bias_path}"
            )

    @classmethod
    def from_checkpoints(
        cls,
        best_ckpt: Path,
        latest_ckpt: Path,
        device: str,
        bias_path: Optional[Path] = None,
        use_tta: bool = True,
        require_bias_file: bool = False,
    ) -> "CalibratedEngine":
        best_ckpt = Path(best_ckpt)
        latest_ckpt = Path(latest_ckpt)

        def _load(path: Path, key: str):
            ckpt = load_checkpoint_secure(path, map_location=device)
            cfg = ckpt["config"]
            m = create_model(
                architecture=cfg["architecture"],
                encoder_name=cfg["encoder_name"],
                encoder_weights=None,
                in_channels=3,
                classes=cfg["classes"],
            )
            m.load_state_dict(ckpt[key])
            m.to(device).eval()
            return m, cfg

        model_best, cfg = _load(best_ckpt, "model_state_dict")
        model_latest, _ = _load(latest_ckpt, "ema_state_dict")

        bias = _DEFAULT_BIAS
        bias_source = "default"
        bp = Path(bias_path) if bias_path else Path("outputs/optimal_bias.json")
        if bp.exists():
            with open(bp) as f:
                data = json.load(f)
            bias = data.get("optimal_bias", _DEFAULT_BIAS)
            bias_source = str(bp)
            LOGGER.info("Loaded optimal bias from %s", bp)
        else:
            if require_bias_file:
                raise FileNotFoundError(f"Bias file required but missing: {bp}")
            LOGGER.warning(
                "Using default bias (run bias_search.py to tune): %s", _DEFAULT_BIAS
            )

        engine = cls(
            model_best=model_best,
            model_latest=model_latest,
            device=device,
            image_size=cfg.get("image_size", 768),
            bias=bias,
            use_tta=use_tta,
            bias_path=bp if bp.exists() else None,
            require_bias_file=False,
        )
        engine.bias_source = bias_source
        engine._checkpoint_meta = {
            "best_ckpt": str(best_ckpt),
            "latest_ckpt": str(latest_ckpt),
            "best_sha256": file_sha256(best_ckpt),
            "latest_sha256": file_sha256(latest_ckpt),
            "bias_source": bias_source,
            "bias": bias,
        }
        return engine

    # ── Core Inference ────────────────────────────────────────────────────────

    @torch.no_grad()
    def _forward_ensemble(self, x: torch.Tensor) -> torch.Tensor:
        """Weighted ensemble logits (B, C, H, W) before bias."""

        def _pred(model, imgs):
            with torch.amp.autocast(device_type="cuda", enabled=(self.device == "cuda")):
                return model(imgs).float()

        logits = self.w_best * _pred(self.model_best, x) + self.w_latest * _pred(self.model_latest, x)

        if self.use_tta:
            x_h = torch.flip(x, [3])
            l_h = torch.flip(
                self.w_best * _pred(self.model_best, x_h) + self.w_latest * _pred(self.model_latest, x_h),
                [3],
            )
            x_v = torch.flip(x, [2])
            l_v = torch.flip(
                self.w_best * _pred(self.model_best, x_v) + self.w_latest * _pred(self.model_latest, x_v),
                [2],
            )
            logits = (logits + l_h + l_v) / 3.0

        return logits

    def _biased_logits(self, logits: torch.Tensor) -> torch.Tensor:
        return logits + self.bias

    def _calibrated_predict(self, logits: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        """Apply bias → argmax. Returns (preds, probs)."""
        biased = self._biased_logits(logits)
        probs = F.softmax(biased, dim=1)
        preds = biased.argmax(dim=1)
        return preds, probs

    def _ensemble_forward_np(self, batch_t: torch.Tensor) -> np.ndarray:
        """Run ensemble on a batch tensor; return biased logits numpy (B, C, H, W)."""
        logits = self._biased_logits(self._forward_ensemble(batch_t))
        return logits.cpu().numpy()

    @torch.no_grad()
    def predict_batch(
        self,
        images: torch.Tensor,
        postprocess: bool = True,
        strict_postprocess: bool = False,
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        Returns:
          preds:  (B, H, W) uint8 class indices
          probs:  (B, C, H, W) float32 softmax probabilities
        """
        images = images.to(self.device, non_blocking=True)
        raw_logits = self._forward_ensemble(images)
        biased_logits = self._biased_logits(raw_logits)
        preds, probs = self._calibrated_predict(raw_logits)

        preds_np = preds.cpu().numpy().astype(np.uint8)
        probs_np = probs.cpu().numpy()
        logits_np = biased_logits.cpu().numpy()

        if postprocess:
            for b in range(preds_np.shape[0]):
                mask = preds_np[b]
                mask = road_gap_fill(mask)
                mask = postprocess_mask(
                    mask,
                    logits_np[b],
                    strict=strict_postprocess,
                )
                mask = bridge_recovery_from_builtup(mask)
                preds_np[b] = mask

        return preds_np, probs_np

    @torch.no_grad()
    def predict_patch(
        self,
        image: Union[torch.Tensor, np.ndarray],
        postprocess: bool = True,
        strict_postprocess: bool = False,
        pixel_size_m: float | None = None,
    ) -> tuple[np.ndarray, dict]:
        """
        Predict on a single patch.

        Args:
            image: (3, H, W) normalized tensor or (H, W, 3) uint8 RGB.
        Returns:
            pred_mask (H, W) uint8, stats dict
        """
        if isinstance(image, np.ndarray):
            if image.ndim == 3 and image.shape[2] == 3:
                tensor = normalize_patch_rgb(image, _IMAGENET_MEAN, _IMAGENET_STD).unsqueeze(0)
            else:
                raise ValueError("Expected HWC uint8 RGB array")
        else:
            tensor = image.unsqueeze(0) if image.dim() == 3 else image

        preds, _ = self.predict_batch(tensor, postprocess=postprocess, strict_postprocess=strict_postprocess)
        mask = preds[0]
        gsd = pixel_size_m if pixel_size_m is not None else float(
            load_platform_config().geospatial.get("default_pixel_size_m", 0.3)
        )
        return mask, self.patch_stats(mask, pixel_size_m=gsd)

    @torch.no_grad()
    def predict_large(
        self,
        image_rgb: np.ndarray,
        patch_size: int | None = None,
        overlap: int | None = None,
        postprocess: bool = True,
        strict_postprocess: bool = False,
        batch_size: int = 4,
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        Sliding-window inference on an arbitrary-size RGB orthomosaic.

        Returns:
            pred_mask (H, W) uint8
            logit_acc (C, H, W) float32 averaged biased logits (for confidence maps)
        """
        if image_rgb.ndim == 3 and image_rgb.shape[2] == 4:
            image_rgb = image_rgb[:, :, :3]

        patch_size = patch_size or self.image_size
        overlap = overlap if overlap is not None else max(32, patch_size // 6)

        h, w = image_rgb.shape[:2]
        logit_acc = np.zeros((NUM_CLASSES, h, w), dtype=np.float32)
        count_acc = np.zeros((h, w), dtype=np.float32)

        batch_tensors: list[torch.Tensor] = []
        batch_meta: list[tuple[int, int, int, int]] = []

        def _flush() -> None:
            if not batch_tensors:
                return
            batch = torch.stack(batch_tensors).to(self.device)
            logits_np = self._ensemble_forward_np(batch)
            for j, (r, c, ph, pw) in enumerate(batch_meta):
                accumulate_logits(logit_acc, count_acc, logits_np[j], r, c, ph, pw)
            batch_tensors.clear()
            batch_meta.clear()

        for r, c, patch, ph, pw in iter_tiles(image_rgb, patch_size, overlap):
            batch_tensors.append(normalize_patch_rgb(patch, _IMAGENET_MEAN, _IMAGENET_STD))
            batch_meta.append((r, c, ph, pw))
            if len(batch_tensors) >= batch_size:
                _flush()
        _flush()

        logit_acc = finalize_logits(logit_acc, count_acc)
        mask = logit_acc.argmax(axis=0).astype(np.uint8)

        if postprocess:
            mask = postprocess_mask(mask, logit_acc, strict=strict_postprocess)

        return mask, logit_acc

    @torch.no_grad()
    def predict_tiff(
        self,
        tiff_path: Union[str, Path],
        output_path: Union[str, Path] | None = None,
        postprocess: bool = True,
        strict_postprocess: bool = False,
        patch_size: int | None = None,
        overlap: int | None = None,
        progress_callback: Callable[[float, str], None] | None = None,
    ) -> tuple[np.ndarray, dict]:
        """
        Windowed inference on a GeoTIFF; optionally write a georeferenced class mask.

        Returns:
            pred_mask (H, W) uint8, metadata dict (CRS, transform, pixel_size_m)
        """
        tiff_path = Path(tiff_path)
        patch_size = patch_size or self.image_size
        overlap = overlap if overlap is not None else max(32, patch_size // 6)
        stride = max(1, patch_size - overlap)

        cfg = load_platform_config()
        allowed_epsg = {int(v) for v in cfg.geospatial.get("allowed_epsg", [])}

        with rasterio.open(tiff_path) as src:
            if src.crs is None:
                raise ValueError(f"Input TIFF missing CRS: {tiff_path}")
            epsg = src.crs.to_epsg()
            if allowed_epsg and epsg not in allowed_epsg:
                raise ValueError(f"Unexpected EPSG {epsg}; allowed={sorted(allowed_epsg)}")

            transform = src.transform
            pixel_size_m = pixel_size_from_transform(transform)
            h, w = src.height, src.width
            pred_mask = np.zeros((h, w), dtype=np.uint8)
            logit_acc = np.zeros((NUM_CLASSES, h, w), dtype=np.float32)
            count_acc = np.zeros((h, w), dtype=np.float32)

            batch_tensors: list[torch.Tensor] = []
            batch_meta: list[tuple[int, int, int, int]] = []

            def _flush() -> None:
                if not batch_tensors:
                    return
                batch = torch.stack(batch_tensors).to(self.device)
                logits_np = self._ensemble_forward_np(batch)
                for j, (row, col, ph, pw) in enumerate(batch_meta):
                    accumulate_logits(logit_acc, count_acc, logits_np[j], row, col, ph, pw)
                batch_tensors.clear()
                batch_meta.clear()

            from src.inference.tiling import count_tiles, tile_positions

            rows = tile_positions(h, patch_size, stride)
            cols = tile_positions(w, patch_size, stride)
            total_tiles = count_tiles(h, w, patch_size, overlap)
            done_tiles = 0

            for row in rows:
                for col in cols:
                    win_h = min(patch_size, h - row)
                    win_w = min(patch_size, w - col)
                    window = Window(col, row, win_w, win_h)
                    patch = src.read([1, 2, 3], window=window).transpose(1, 2, 0).astype(np.uint8)
                    if win_h < patch_size or win_w < patch_size:
                        padded = np.zeros((patch_size, patch_size, 3), dtype=np.uint8)
                        padded[:win_h, :win_w] = patch
                        patch = padded
                    batch_tensors.append(normalize_patch_rgb(patch, _IMAGENET_MEAN, _IMAGENET_STD))
                    batch_meta.append((row, col, win_h, win_w))
                    done_tiles += 1
                    if len(batch_tensors) >= 4:
                        _flush()
                        if progress_callback is not None:
                            progress_callback(
                                done_tiles / total_tiles,
                                f"Inference {done_tiles}/{total_tiles} tiles on {self.device}",
                            )
            _flush()
            if progress_callback is not None:
                progress_callback(0.92, "Finalizing mask…")

            logit_acc = finalize_logits(logit_acc, count_acc)
            pred_mask = logit_acc.argmax(axis=0).astype(np.uint8)
            if postprocess:
                # Full bridge recovery uses 101px dilations — minutes on 8k×8k demo tiles.
                large = h * w > 25_000_000
                if progress_callback is not None and large:
                    progress_callback(0.93, "Post-processing (fast path for large ortho)…")
                pred_mask = postprocess_mask(
                    pred_mask,
                    logit_acc,
                    use_bridge_recovery=not large,
                )

            meta = {
                "crs": str(src.crs),
                "epsg": epsg,
                "transform": list(transform)[:6],
                "pixel_size_m": pixel_size_m,
                "width": w,
                "height": h,
            }

            if output_path is not None:
                out_path = Path(output_path)
                out_path.parent.mkdir(parents=True, exist_ok=True)
                profile = src.profile.copy()
                profile.update(count=1, dtype="uint8", compress="lzw", nodata=0)
                with rasterio.open(out_path, "w", **profile) as dst:
                    dst.write(pred_mask, 1)

        stats = self.patch_stats(pred_mask, pixel_size_m=pixel_size_m)
        return pred_mask, {**meta, "stats": stats}

    def patch_stats(self, mask: np.ndarray, pixel_size_m: float | None = None) -> dict:
        """Compute quantitative infrastructure stats for a single patch."""
        if pixel_size_m is None:
            pixel_size_m = float(load_platform_config().geospatial.get("default_pixel_size_m", 0.3))

        rooftop_mask = classify_rooftops(mask)
        stats = get_infrastructure_summary(mask, rooftop_mask)
        px_area = pixel_size_m * pixel_size_m

        road_px = int((mask == 1).sum())
        water_px = int((mask == 4).sum())
        bu_px = int((mask == 3).sum())

        stats["pixel_size_m"] = pixel_size_m
        stats["road_length_m"] = round(road_px * pixel_size_m, 1)
        stats["water_area_m2"] = round(water_px * px_area, 1)
        stats["builtup_area_m2"] = round(bu_px * px_area, 1)
        return stats

    def provenance(self) -> dict:
        """Return checkpoint/bias provenance when loaded via from_checkpoints."""
        return getattr(self, "_checkpoint_meta", {})
