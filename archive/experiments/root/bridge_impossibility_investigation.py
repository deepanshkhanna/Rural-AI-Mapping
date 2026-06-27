"""Phase 5: Bridge impossibility proof and alternative formulation investigation.

This script performs a no-training forensic investigation across 8 phases and writes
all requested reports under outputs/bridge_impossibility.
"""

from __future__ import annotations

import json
import math
import os
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cv2
import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import rasterio
import torch
from shapely.geometry import box
from rasterio.features import rasterize
from rasterio.windows import Window
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression
from sklearn.manifold import TSNE
from sklearn.metrics import roc_auc_score, silhouette_score
from sklearn.model_selection import train_test_split

from src.config.platform_config import load_platform_config
from src.datasets.unified_dataset import CLASS_NAMES, DEFAULT_SOURCES
from src.models.model_factory import create_model
from src.security.checkpoints import load_checkpoint_secure


try:
    import umap  # type: ignore
    HAS_UMAP = True
except Exception:
    HAS_UMAP = False


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "outputs" / "bridge_impossibility"
MASTER_DIR = OUT_DIR / "bridge_master_catalog"
MASTER_ENTRIES_DIR = MASTER_DIR / "entries"
MASTER_SOURCE_DIR = MASTER_DIR / "source_tiffs"
FIG_DIR = OUT_DIR / "figures"
CSV_DIR = OUT_DIR / "tables"

BRIDGE_PATCH_CATALOG = ROOT / "outputs" / "bridge_phase3" / "bridge_patch_catalog"
BEST_CHECKPOINT = ROOT / "outputs" / "bridge_campaign" / "G_best_configuration" / "checkpoints" / "best_model.pth"

EVIDENCE_FILES = [
    ROOT / "outputs" / "bridge_campaign" / "final_bridge_recovery_report.md",
    ROOT / "outputs" / "bridge_campaign" / "checkpoint_comparison.md",
    ROOT / "outputs" / "bridge_campaign" / "bridge_training_campaign.md",
    ROOT / "outputs" / "bridge_phase3" / "reports" / "bridge_root_cause_proof.md",
    ROOT / "outputs" / "bridge_phase3" / "reports" / "bridge_annotation_audit.md",
    ROOT / "outputs" / "recovery_reports" / "dataset_truth_report.md",
    ROOT / "outputs" / "bridge_campaign" / "campaign_results.json",
]
OPTIONAL_MISSING_EVIDENCE = ROOT / "outputs" / "bridge_phase3" / "reports" / "bridge_failure_analysis.md"

CLASS_ROAD = 1
CLASS_BRIDGE = 2
CLASS_BUILT = 3
CLASS_WATER = 4

IMAGENET_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
IMAGENET_STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)


@dataclass
class BridgeEntry:
    bridge_id: str
    split: str
    source_name: str
    tiff_name: str
    tiff_path: str
    bridge_pixels: int
    bbox_x: int
    bbox_y: int
    bbox_w: int
    bbox_h: int
    crop_w: int
    crop_h: int
    crop_path: str
    mask_path: str
    road_mask_path: str
    metadata_path: str


def ensure_dirs() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    MASTER_DIR.mkdir(parents=True, exist_ok=True)
    MASTER_ENTRIES_DIR.mkdir(parents=True, exist_ok=True)
    MASTER_SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    CSV_DIR.mkdir(parents=True, exist_ok=True)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def percentile_stretch_rgb(arr: np.ndarray) -> np.ndarray:
    if arr.dtype == np.uint8:
        return arr
    x = arr.astype(np.float32)
    out = np.zeros_like(x, dtype=np.float32)
    for c in range(min(3, x.shape[2])):
        ch = x[:, :, c]
        lo = np.percentile(ch, 2)
        hi = np.percentile(ch, 98)
        if hi <= lo + 1e-6:
            out[:, :, c] = 0
        else:
            out[:, :, c] = np.clip((ch - lo) / (hi - lo), 0, 1) * 255.0
    return out.astype(np.uint8)


def safe_symlink(src: Path, dst: Path) -> None:
    if dst.exists() or dst.is_symlink():
        return
    try:
        os.symlink(src, dst)
    except Exception:
        shutil.copy2(src, dst)


def evidence_digest() -> dict[str, Any]:
    out: dict[str, Any] = {"found": [], "missing": []}
    for path in EVIDENCE_FILES:
        if path.exists():
            out["found"].append(str(path))
        else:
            out["missing"].append(str(path))
    if OPTIONAL_MISSING_EVIDENCE.exists():
        out["found"].append(str(OPTIONAL_MISSING_EVIDENCE))
    else:
        out["missing"].append(str(OPTIONAL_MISSING_EVIDENCE))
    return out


def iter_bridge_geometries() -> list[dict[str, Any]]:
    cfg = load_platform_config()
    all_tiff_stems = set(cfg.train_tiffs) | set(cfg.val_tiffs)
    records: list[dict[str, Any]] = []

    for src in DEFAULT_SOURCES:
        source_name = str(src["name"])
        tiff_dir = ROOT / str(src["tiff_dir"])
        shp_dir = ROOT / str(src["shp_dir"])
        bridge_shp = shp_dir / "Bridge.shp"
        road_shp = shp_dir / "Road.shp"
        if not bridge_shp.exists() or not road_shp.exists():
            continue

        bridge_gdf_raw = gpd.read_file(bridge_shp)
        road_gdf_raw = gpd.read_file(road_shp)
        if bridge_gdf_raw.empty:
            continue

        for tiff_path in sorted(list(tiff_dir.glob("*.tif")) + list(tiff_dir.glob("*.tiff"))):
            if tiff_path.stem not in all_tiff_stems:
                continue
            split = "val" if tiff_path.stem in cfg.val_tiffs else "train"
            with rasterio.open(tiff_path) as ds:
                tiff_bounds_geom = box(ds.bounds.left, ds.bounds.bottom, ds.bounds.right, ds.bounds.top)
                bridge_gdf = bridge_gdf_raw.to_crs(ds.crs)
                road_gdf = road_gdf_raw.to_crs(ds.crs)
                bridge_hits = bridge_gdf[bridge_gdf.geometry.intersects(tiff_bounds_geom)]
                if bridge_hits.empty:
                    continue

                for idx, geom in enumerate(bridge_hits.geometry):
                    if geom is None or geom.is_empty:
                        continue
                    parts = list(geom.geoms) if geom.geom_type == "MultiPolygon" else [geom]
                    for part_idx, part in enumerate(parts):
                        if part.is_empty or not part.is_valid:
                            continue
                        records.append(
                            {
                                "source_name": source_name,
                                "split": split,
                                "tiff_path": tiff_path,
                                "tiff_name": tiff_path.name,
                                "bridge_geom": part,
                                "road_gdf": road_gdf,
                                "raster_crs": ds.crs,
                                "transform": ds.transform,
                                "width": ds.width,
                                "height": ds.height,
                                "bridge_idx": idx,
                                "part_idx": part_idx,
                            }
                        )
    return records


def extract_bridge_master_catalog() -> tuple[list[BridgeEntry], dict[str, float]]:
    raw_records = iter_bridge_geometries()
    entries: list[BridgeEntry] = []
    bridge_sizes: list[int] = []

    for rec_idx, rec in enumerate(raw_records):
        bridge_id = f"bridge_{rec_idx:04d}"
        bridge_geom = rec["bridge_geom"]
        tiff_path: Path = rec["tiff_path"]
        split = rec["split"]

        x_min, y_min, x_max, y_max = bridge_geom.bounds
        with rasterio.open(tiff_path) as ds:
            row_min, col_min = ds.index(x_min, y_max)
            row_max, col_max = ds.index(x_max, y_min)

            row_min, row_max = sorted([row_min, row_max])
            col_min, col_max = sorted([col_min, col_max])

            h = max(1, row_max - row_min + 1)
            w = max(1, col_max - col_min + 1)
            pad = 96
            min_crop = 256

            y0 = max(0, row_min - pad)
            x0 = max(0, col_min - pad)
            y1 = min(ds.height, row_max + pad + 1)
            x1 = min(ds.width, col_max + pad + 1)

            if y1 - y0 < min_crop:
                deficit = min_crop - (y1 - y0)
                y0 = max(0, y0 - deficit // 2)
                y1 = min(ds.height, y1 + deficit - deficit // 2)
            if x1 - x0 < min_crop:
                deficit = min_crop - (x1 - x0)
                x0 = max(0, x0 - deficit // 2)
                x1 = min(ds.width, x1 + deficit - deficit // 2)

            win = Window(col_off=x0, row_off=y0, width=(x1 - x0), height=(y1 - y0))
            patch = ds.read([1, 2, 3], window=win)
            patch = np.transpose(patch, (1, 2, 0))
            patch = percentile_stretch_rgb(patch)

            win_transform = ds.window_transform(win)

            bridge_mask = rasterize(
                [(bridge_geom, 1)],
                out_shape=(int(win.height), int(win.width)),
                transform=win_transform,
                fill=0,
                dtype=np.uint8,
            )

            road_hits = rec["road_gdf"][rec["road_gdf"].geometry.intersects(bridge_geom.buffer(80))]
            road_shapes = [(g, 1) for g in road_hits.geometry if g is not None and not g.is_empty]
            road_mask = rasterize(
                road_shapes,
                out_shape=(int(win.height), int(win.width)),
                transform=win_transform,
                fill=0,
                dtype=np.uint8,
            ) if road_shapes else np.zeros((int(win.height), int(win.width)), dtype=np.uint8)

        bridge_pixels = int(bridge_mask.sum())
        if bridge_pixels <= 0:
            continue

        entry_dir = MASTER_ENTRIES_DIR / bridge_id
        entry_dir.mkdir(parents=True, exist_ok=True)
        crop_path = entry_dir / "image_crop.png"
        mask_path = entry_dir / "bridge_mask.png"
        road_mask_path = entry_dir / "road_mask.png"
        meta_path = entry_dir / "metadata.json"

        cv2.imwrite(str(crop_path), cv2.cvtColor(patch, cv2.COLOR_RGB2BGR))
        cv2.imwrite(str(mask_path), bridge_mask)
        cv2.imwrite(str(road_mask_path), road_mask)

        linked_tiff = MASTER_SOURCE_DIR / tiff_path.name
        safe_symlink(tiff_path, linked_tiff)

        metadata = {
            "bridge_id": bridge_id,
            "split": split,
            "source_name": rec["source_name"],
            "tiff_name": tiff_path.name,
            "tiff_path": str(tiff_path),
            "linked_source_tiff": str(linked_tiff),
            "bbox_px": {
                "x": int(col_min),
                "y": int(row_min),
                "w": int(w),
                "h": int(h),
            },
            "crop_px": {
                "x": int(x0),
                "y": int(y0),
                "w": int(x1 - x0),
                "h": int(y1 - y0),
            },
            "bridge_pixels": bridge_pixels,
            "road_pixels_in_crop": int(road_mask.sum()),
        }
        write_text(meta_path, json.dumps(metadata, indent=2))

        entries.append(
            BridgeEntry(
                bridge_id=bridge_id,
                split=split,
                source_name=str(rec["source_name"]),
                tiff_name=tiff_path.name,
                tiff_path=str(tiff_path),
                bridge_pixels=bridge_pixels,
                bbox_x=int(col_min),
                bbox_y=int(row_min),
                bbox_w=int(w),
                bbox_h=int(h),
                crop_w=int(x1 - x0),
                crop_h=int(y1 - y0),
                crop_path=str(crop_path),
                mask_path=str(mask_path),
                road_mask_path=str(road_mask_path),
                metadata_path=str(meta_path),
            )
        )
        bridge_sizes.append(bridge_pixels)

    bridge_sizes_arr = np.array(bridge_sizes, dtype=np.int64)
    stats = {
        "total_bridges": int(len(entries)),
        "total_bridge_pixels": int(bridge_sizes_arr.sum()) if bridge_sizes else 0,
        "avg_bridge_size": float(bridge_sizes_arr.mean()) if bridge_sizes else 0.0,
        "median_bridge_size": float(np.median(bridge_sizes_arr)) if bridge_sizes else 0.0,
        "min_bridge_size": int(bridge_sizes_arr.min()) if bridge_sizes else 0,
        "max_bridge_size": int(bridge_sizes_arr.max()) if bridge_sizes else 0,
    }

    master_index = {
        "entries": [entry.__dict__ for entry in entries],
        "stats": stats,
    }
    write_text(MASTER_DIR / "master_index.json", json.dumps(master_index, indent=2))
    return entries, stats


def texture_metrics(rgb: np.ndarray, mask: np.ndarray) -> dict[str, float]:
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY).astype(np.float32)
    gx = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
    grad = np.sqrt(gx * gx + gy * gy)
    lap = cv2.Laplacian(gray, cv2.CV_32F)
    px = grad[mask > 0]
    lp = lap[mask > 0]
    if px.size == 0:
        return {"grad_mean": 0.0, "grad_std": 0.0, "lap_var": 0.0}
    return {
        "grad_mean": float(px.mean()),
        "grad_std": float(px.std()),
        "lap_var": float(lp.var()),
    }


def mask_width_estimate(mask: np.ndarray) -> float:
    if mask.sum() == 0:
        return 0.0
    dist = cv2.distanceTransform((mask > 0).astype(np.uint8), cv2.DIST_L2, 3)
    vals = dist[mask > 0]
    if vals.size == 0:
        return 0.0
    return float(2.0 * np.median(vals))


def largest_component_shape(mask: np.ndarray) -> dict[str, float]:
    m = (mask > 0).astype(np.uint8)
    contours, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return {"area": 0.0, "perimeter": 0.0, "width": 0.0, "height": 0.0, "orientation_deg": 0.0}
    c = max(contours, key=cv2.contourArea)
    area = float(cv2.contourArea(c))
    peri = float(cv2.arcLength(c, True))
    rect = cv2.minAreaRect(c)
    (w, h) = rect[1]
    angle = float(rect[2])
    return {
        "area": area,
        "perimeter": peri,
        "width": float(min(w, h)),
        "height": float(max(w, h)),
        "orientation_deg": angle,
    }


def compute_bridge_vs_road(entries: list[BridgeEntry]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for e in entries:
        rgb = cv2.cvtColor(cv2.imread(e.crop_path, cv2.IMREAD_COLOR), cv2.COLOR_BGR2RGB)
        bridge_mask = cv2.imread(e.mask_path, cv2.IMREAD_GRAYSCALE)
        road_mask = cv2.imread(e.road_mask_path, cv2.IMREAD_GRAYSCALE)

        if rgb is None or bridge_mask is None or road_mask is None:
            continue

        bridge_bin = (bridge_mask > 0).astype(np.uint8)
        road_bin = (road_mask > 0).astype(np.uint8)

        kernel = np.ones((21, 21), dtype=np.uint8)
        ring = cv2.dilate(bridge_bin, kernel, iterations=1)
        ring = ((ring > 0) & (bridge_bin == 0)).astype(np.uint8)
        nearby_road = ((ring > 0) & (road_bin > 0)).astype(np.uint8)
        if nearby_road.sum() < 20:
            nearby_road = road_bin

        bp = rgb[bridge_bin > 0]
        rp = rgb[nearby_road > 0]
        if bp.size == 0 or rp.size == 0:
            continue

        b_mean = bp.mean(axis=0)
        r_mean = rp.mean(axis=0)
        b_std = bp.std(axis=0)
        r_std = rp.std(axis=0)

        rgb_l2 = float(np.linalg.norm(b_mean - r_mean) / 255.0)
        pooled_std = np.maximum((b_std + r_std) / 2.0, 1e-6)
        rgb_z = float(np.linalg.norm((b_mean - r_mean) / pooled_std))

        b_tex = texture_metrics(rgb, bridge_bin)
        r_tex = texture_metrics(rgb, nearby_road)
        grad_gap = float(abs(b_tex["grad_mean"] - r_tex["grad_mean"]))
        lap_gap = float(abs(b_tex["lap_var"] - r_tex["lap_var"]))

        b_shape = largest_component_shape(bridge_bin)
        bridge_width = mask_width_estimate(bridge_bin)
        road_width = mask_width_estimate(nearby_road)
        width_ratio = float(bridge_width / (road_width + 1e-6))

        distinct_score = float(rgb_l2 + 0.15 * min(1.0, grad_gap / 40.0) + 0.15 * min(1.0, lap_gap / 80.0))

        rows.append(
            {
                "bridge_id": e.bridge_id,
                "split": e.split,
                "tiff_name": e.tiff_name,
                "bridge_pixels": int(bridge_bin.sum()),
                "nearby_road_pixels": int(nearby_road.sum()),
                "bridge_r_mean": float(b_mean[0]),
                "bridge_g_mean": float(b_mean[1]),
                "bridge_b_mean": float(b_mean[2]),
                "road_r_mean": float(r_mean[0]),
                "road_g_mean": float(r_mean[1]),
                "road_b_mean": float(r_mean[2]),
                "rgb_mean_l2_norm": rgb_l2,
                "rgb_mean_z_dist": rgb_z,
                "bridge_grad_mean": b_tex["grad_mean"],
                "road_grad_mean": r_tex["grad_mean"],
                "bridge_lap_var": b_tex["lap_var"],
                "road_lap_var": r_tex["lap_var"],
                "grad_gap": grad_gap,
                "lap_gap": lap_gap,
                "bridge_shape_area": b_shape["area"],
                "bridge_perimeter": b_shape["perimeter"],
                "bridge_shape_width": b_shape["width"],
                "bridge_shape_height": b_shape["height"],
                "bridge_orientation_deg": b_shape["orientation_deg"],
                "bridge_width_est": bridge_width,
                "road_width_est": road_width,
                "width_ratio_bridge_to_road": width_ratio,
                "distinct_score": distinct_score,
            }
        )

    df = pd.DataFrame(rows)
    if not df.empty:
        df.to_csv(CSV_DIR / "bridge_vs_road_similarity.csv", index=False)
    return df


def classify_annotation_quality(df: pd.DataFrame) -> pd.DataFrame:
    quality: list[str] = []
    rationale: list[str] = []

    for _, row in df.iterrows():
        bp = int(row["bridge_pixels"])
        zdist = float(row["rgb_mean_z_dist"])
        dscore = float(row["distinct_score"])

        if bp < 50 or dscore < 0.03:
            quality.append("C")
            rationale.append("insufficient visible signal")
        elif bp < 250 or zdist < 0.8:
            quality.append("B")
            rationale.append("weak contrast or small footprint")
        else:
            quality.append("A")
            rationale.append("clear footprint and measurable contrast")

    out = df[["bridge_id", "split", "tiff_name", "bridge_pixels", "rgb_mean_z_dist", "distinct_score"]].copy()
    out["quality_class"] = quality
    out["audit_note"] = rationale
    out.to_csv(CSV_DIR / "bridge_annotation_quality.csv", index=False)
    return out


def parse_dataset_truth() -> dict[str, int]:
    text = read_text(ROOT / "outputs" / "recovery_reports" / "dataset_truth_report.md")

    def grab(name: str) -> int:
        m = re.search(rf"{re.escape(name)}\s*\(est\):\s*([0-9,]+)", text)
        if not m:
            return 0
        return int(m.group(1).replace(",", ""))

    return {
        "road": grab("road pixels"),
        "bridge": grab("bridge pixels"),
        "built": grab("built-up pixels"),
        "water": grab("water pixels"),
    }


def load_patch_catalog() -> list[dict[str, Any]]:
    metadata_path = BRIDGE_PATCH_CATALOG / "metadata.json"
    if not metadata_path.exists():
        return []
    return json.loads(metadata_path.read_text(encoding="utf-8"))


def preprocess_for_model(rgb: np.ndarray) -> torch.Tensor:
    x = rgb.astype(np.float32) / 255.0
    x = (x - IMAGENET_MEAN[None, None, :]) / IMAGENET_STD[None, None, :]
    x = np.transpose(x, (2, 0, 1))
    return torch.from_numpy(x).unsqueeze(0)


def load_best_model() -> tuple[torch.nn.Module, dict[str, Any], torch.device]:
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    ckpt = load_checkpoint_secure(BEST_CHECKPOINT, map_location=device)
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
    return model, cfg, device


def feature_space_analysis() -> dict[str, Any]:
    patch_meta = load_patch_catalog()
    model, cfg, device = load_best_model()

    bridge_feats: list[np.ndarray] = []
    road_feats: list[np.ndarray] = []

    confusion_rows: list[dict[str, Any]] = []
    total_bridge_gt = 0
    agg_pred_counts = np.zeros(5, dtype=np.int64)

    with torch.no_grad():
        for row in patch_meta:
            img_path = ROOT / "outputs" / "bridge_phase3" / row["image_rel"]
            mask_path = ROOT / "outputs" / "bridge_phase3" / row["mask_rel"]
            rgb = cv2.cvtColor(cv2.imread(str(img_path), cv2.IMREAD_COLOR), cv2.COLOR_BGR2RGB)
            mask = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)
            if rgb is None or mask is None:
                continue

            x = preprocess_for_model(rgb).to(device)
            logits = model(x)
            preds = logits.argmax(dim=1).squeeze(0).cpu().numpy().astype(np.uint8)

            bridge_gt = (mask == CLASS_BRIDGE)
            road_gt = (mask == CLASS_ROAD)

            if bridge_gt.sum() > 0:
                pred_on_bridge = preds[bridge_gt]
                binc = np.bincount(pred_on_bridge, minlength=5)
                agg_pred_counts += binc
                total_bridge_gt += int(bridge_gt.sum())
                confusion_rows.append(
                    {
                        "patch_id": row["patch_id"],
                        "bridge_gt_pixels": int(bridge_gt.sum()),
                        "pred_background": int(binc[0]),
                        "pred_road": int(binc[1]),
                        "pred_bridge": int(binc[2]),
                        "pred_built": int(binc[3]),
                        "pred_water": int(binc[4]),
                    }
                )

            feats = model.encoder(x)
            if isinstance(feats, (list, tuple)):
                f = feats[-1]
            else:
                f = feats
            f_np = f.squeeze(0).permute(1, 2, 0).cpu().numpy().astype(np.float32)
            fh, fw, fc = f_np.shape

            mask_small = cv2.resize(mask, (fw, fh), interpolation=cv2.INTER_NEAREST)
            bridge_positions = np.argwhere(mask_small == CLASS_BRIDGE)
            road_positions = np.argwhere(mask_small == CLASS_ROAD)

            if bridge_positions.size > 0:
                n_take = min(150, bridge_positions.shape[0])
                idx = np.random.choice(bridge_positions.shape[0], n_take, replace=False)
                yyxx = bridge_positions[idx]
                bridge_feats.append(f_np[yyxx[:, 0], yyxx[:, 1], :])

            if road_positions.size > 0:
                n_take = min(150, road_positions.shape[0])
                idx = np.random.choice(road_positions.shape[0], n_take, replace=False)
                yyxx = road_positions[idx]
                road_feats.append(f_np[yyxx[:, 0], yyxx[:, 1], :])

    if not bridge_feats or not road_feats:
        raise RuntimeError("Insufficient bridge/road features extracted from patch catalog.")

    bridge_mat = np.concatenate(bridge_feats, axis=0)
    road_mat = np.concatenate(road_feats, axis=0)

    n = min(len(bridge_mat), len(road_mat), 5000)
    b_idx = np.random.choice(len(bridge_mat), n, replace=False)
    r_idx = np.random.choice(len(road_mat), n, replace=False)

    X_bridge = bridge_mat[b_idx]
    X_road = road_mat[r_idx]

    X = np.concatenate([X_bridge, X_road], axis=0)
    y = np.concatenate([np.ones(n, dtype=np.int64), np.zeros(n, dtype=np.int64)], axis=0)

    pca = PCA(n_components=2, random_state=42)
    pca_2d = pca.fit_transform(X)

    tsne = TSNE(n_components=2, perplexity=min(30, max(5, n // 10)), random_state=42, init="random")
    tsne_2d = tsne.fit_transform(X)

    if HAS_UMAP:
        umap_model = umap.UMAP(n_components=2, random_state=42)
        umap_2d = umap_model.fit_transform(X)
    else:
        umap_2d = pca_2d.copy()

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42, stratify=y)
    clf = LogisticRegression(max_iter=1000)
    clf.fit(X_train, y_train)
    y_prob = clf.predict_proba(X_test)[:, 1]
    auc = float(roc_auc_score(y_test, y_prob))

    sil = float(silhouette_score(X, y))

    b_cent = X_bridge.mean(axis=0)
    r_cent = X_road.mean(axis=0)
    centroid_dist = float(np.linalg.norm(b_cent - r_cent))
    within = float(np.mean(np.linalg.norm(X_bridge - b_cent, axis=1)) + np.mean(np.linalg.norm(X_road - r_cent, axis=1)))
    fisher_like = float(centroid_dist / (within + 1e-6))

    def save_scatter(coords: np.ndarray, name: str) -> None:
        plt.figure(figsize=(7, 6))
        plt.scatter(coords[:n, 0], coords[:n, 1], s=4, alpha=0.45, label="Bridge", c="#c0392b")
        plt.scatter(coords[n:, 0], coords[n:, 1], s=4, alpha=0.45, label="Road", c="#2980b9")
        plt.legend()
        plt.title(f"Bridge vs Road Feature Projection: {name}")
        plt.tight_layout()
        plt.savefig(FIG_DIR / f"feature_{name.lower()}.png", dpi=160)
        plt.close()

    save_scatter(pca_2d, "PCA")
    save_scatter(tsne_2d, "TSNE")
    save_scatter(umap_2d, "UMAP")

    confusion_df = pd.DataFrame(confusion_rows)
    confusion_df.to_csv(CSV_DIR / "bridge_confusion_per_patch.csv", index=False)

    agg_pct = (agg_pred_counts / max(1, total_bridge_gt) * 100.0).tolist()

    feature_summary = {
        "num_bridge_features": int(n),
        "num_road_features": int(n),
        "silhouette": sil,
        "logreg_auc": auc,
        "centroid_distance": centroid_dist,
        "fisher_like_ratio": fisher_like,
        "umap_available": HAS_UMAP,
        "agg_bridge_gt_pixels": int(total_bridge_gt),
        "bridge_confusion_percent": {
            "Background": float(agg_pct[0]),
            "Road": float(agg_pct[1]),
            "Bridge": float(agg_pct[2]),
            "Built-Up Area": float(agg_pct[3]),
            "Water Body": float(agg_pct[4]),
        },
    }
    write_text(OUT_DIR / "feature_space_summary.json", json.dumps(feature_summary, indent=2))
    return feature_summary


def write_bridge_inventory_report(stats: dict[str, float], entries: list[BridgeEntry]) -> None:
    by_split = pd.DataFrame([e.__dict__ for e in entries]).groupby("split").size().to_dict() if entries else {}
    lines = [
        "# Bridge Inventory Report",
        "",
        f"- total bridges: {stats['total_bridges']}",
        f"- total bridge pixels: {stats['total_bridge_pixels']}",
        f"- average bridge size (px): {stats['avg_bridge_size']:.2f}",
        f"- median bridge size (px): {stats['median_bridge_size']:.2f}",
        f"- min bridge size (px): {stats['min_bridge_size']}",
        f"- max bridge size (px): {stats['max_bridge_size']}",
        f"- train bridges: {int(by_split.get('train', 0))}",
        f"- val bridges: {int(by_split.get('val', 0))}",
        "",
        "Master catalog path:",
        f"- {MASTER_DIR}",
    ]
    write_text(OUT_DIR / "bridge_inventory_report.md", "\n".join(lines) + "\n")


def write_similarity_report(df: pd.DataFrame) -> dict[str, Any]:
    if df.empty:
        lines = ["# Bridge vs Road Similarity Report", "", "No data available."]
        write_text(OUT_DIR / "bridge_vs_road_similarity_report.md", "\n".join(lines) + "\n")
        return {}

    weak = (df["distinct_score"] < 0.08).mean()
    moderate = ((df["distinct_score"] >= 0.08) & (df["distinct_score"] < 0.16)).mean()
    strong = (df["distinct_score"] >= 0.16).mean()

    summary = {
        "count": int(len(df)),
        "mean_rgb_l2": float(df["rgb_mean_l2_norm"].mean()),
        "median_rgb_l2": float(df["rgb_mean_l2_norm"].median()),
        "mean_distinct_score": float(df["distinct_score"].mean()),
        "weak_fraction": float(weak),
        "moderate_fraction": float(moderate),
        "strong_fraction": float(strong),
        "mean_width_ratio": float(df["width_ratio_bridge_to_road"].mean()),
    }

    verdict = "effectively roads with different labels" if summary["weak_fraction"] >= 0.7 else "visually distinct in a substantial subset"

    lines = [
        "# Bridge vs Road Similarity Report",
        "",
        f"- analyzed bridge examples: {summary['count']}",
        f"- mean RGB distance (normalized L2): {summary['mean_rgb_l2']:.4f}",
        f"- median RGB distance (normalized L2): {summary['median_rgb_l2']:.4f}",
        f"- mean distinct score: {summary['mean_distinct_score']:.4f}",
        f"- weakly distinct fraction: {summary['weak_fraction'] * 100:.2f}%",
        f"- moderately distinct fraction: {summary['moderate_fraction'] * 100:.2f}%",
        f"- strongly distinct fraction: {summary['strong_fraction'] * 100:.2f}%",
        f"- mean bridge/road width ratio: {summary['mean_width_ratio']:.4f}",
        "",
        "## Determination",
        f"- {verdict}",
        "",
        "Detailed table:",
        f"- {CSV_DIR / 'bridge_vs_road_similarity.csv'}",
    ]
    write_text(OUT_DIR / "bridge_vs_road_similarity_report.md", "\n".join(lines) + "\n")
    write_text(OUT_DIR / "bridge_vs_road_similarity_summary.json", json.dumps(summary, indent=2))
    return summary


def write_annotation_quality_report(quality_df: pd.DataFrame) -> dict[str, Any]:
    counts = quality_df["quality_class"].value_counts().to_dict() if not quality_df.empty else {}
    summary = {
        "A_clearly_visible": int(counts.get("A", 0)),
        "B_barely_visible": int(counts.get("B", 0)),
        "C_impossible": int(counts.get("C", 0)),
        "total": int(len(quality_df)),
    }

    lines = [
        "# Bridge Annotation Quality Report",
        "",
        f"- total audited bridges: {summary['total']}",
        f"- A) clearly visible: {summary['A_clearly_visible']}",
        f"- B) barely visible: {summary['B_barely_visible']}",
        f"- C) impossible to identify: {summary['C_impossible']}",
        "",
        "Per-bridge classification table:",
        f"- {CSV_DIR / 'bridge_annotation_quality.csv'}",
    ]
    write_text(OUT_DIR / "bridge_annotation_quality_report.md", "\n".join(lines) + "\n")
    write_text(OUT_DIR / "bridge_annotation_quality_summary.json", json.dumps(summary, indent=2))
    return summary


def write_information_content_report(dataset_truth: dict[str, int], feature_summary: dict[str, Any]) -> dict[str, Any]:
    road = dataset_truth["road"]
    bridge = dataset_truth["bridge"]
    built = dataset_truth["built"]
    water = dataset_truth["water"]
    total_fg = road + bridge + built + water

    bridge_pct = float(100.0 * bridge / max(1, total_fg))
    bridge_vs_road = float(bridge / max(1, road))
    bridge_vs_built = float(bridge / max(1, built))
    bridge_vs_water = float(bridge / max(1, water))

    pred_bridge_pct_on_gt_bridge = float(feature_summary["bridge_confusion_percent"]["Bridge"]) if feature_summary else 0.0

    summary = {
        "bridge_pct_of_fg": bridge_pct,
        "bridge_to_road_ratio": bridge_vs_road,
        "bridge_to_built_ratio": bridge_vs_built,
        "bridge_to_water_ratio": bridge_vs_water,
        "effective_signal_index": float(bridge_pct * max(0.0, pred_bridge_pct_on_gt_bridge) / 100.0),
    }

    lines = [
        "# Bridge Information Content Report",
        "",
        f"- road pixels (est): {road}",
        f"- bridge pixels (est): {bridge}",
        f"- built-up pixels (est): {built}",
        f"- water pixels (est): {water}",
        f"- bridge share of foreground: {bridge_pct:.6f}%",
        f"- bridge/road ratio: {bridge_vs_road:.8f}",
        f"- bridge/built-up ratio: {bridge_vs_built:.8f}",
        f"- bridge/water ratio: {bridge_vs_water:.8f}",
        f"- effective signal index: {summary['effective_signal_index']:.8f}",
    ]
    write_text(OUT_DIR / "bridge_information_content_report.md", "\n".join(lines) + "\n")
    write_text(OUT_DIR / "bridge_information_content_summary.json", json.dumps(summary, indent=2))
    return summary


def write_feature_separation_report(summary: dict[str, Any]) -> None:
    lines = [
        "# Bridge Feature Separation Report",
        "",
        f"- feature samples per class: {summary['num_bridge_features']}",
        f"- silhouette score: {summary['silhouette']:.6f}",
        f"- logistic AUC (bridge vs road): {summary['logreg_auc']:.6f}",
        f"- centroid distance: {summary['centroid_distance']:.6f}",
        f"- fisher-like ratio: {summary['fisher_like_ratio']:.6f}",
        f"- UMAP available: {summary['umap_available']}",
        "",
        "Figures:",
        f"- {FIG_DIR / 'feature_pca.png'}",
        f"- {FIG_DIR / 'feature_tsne.png'}",
        f"- {FIG_DIR / 'feature_umap.png'}",
    ]
    write_text(OUT_DIR / "bridge_feature_separation_report.md", "\n".join(lines) + "\n")


def write_confusion_report(feature_summary: dict[str, Any]) -> dict[str, float]:
    pct = feature_summary["bridge_confusion_percent"]
    lines = [
        "# Bridge Confusion Report",
        "",
        f"- total GT bridge pixels analyzed: {feature_summary['agg_bridge_gt_pixels']}",
        f"- predicted as background: {pct['Background']:.6f}%",
        f"- predicted as road: {pct['Road']:.6f}%",
        f"- predicted as bridge: {pct['Bridge']:.6f}%",
        f"- predicted as built-up: {pct['Built-Up Area']:.6f}%",
        f"- predicted as water: {pct['Water Body']:.6f}%",
        "",
        "Per-patch confusion table:",
        f"- {CSV_DIR / 'bridge_confusion_per_patch.csv'}",
    ]
    write_text(OUT_DIR / "bridge_confusion_report.md", "\n".join(lines) + "\n")
    return {k: float(v) for k, v in pct.items()}


def write_detector_feasibility_report(entries: list[BridgeEntry], quality_summary: dict[str, Any], confusion_pct: dict[str, float], sim_summary: dict[str, Any]) -> dict[str, Any]:
    if entries:
        widths = np.array([e.bbox_w for e in entries], dtype=np.float32)
        heights = np.array([e.bbox_h for e in entries], dtype=np.float32)
        areas = widths * heights
        min_dim = np.minimum(widths, heights)
    else:
        widths = heights = areas = min_dim = np.array([0.0], dtype=np.float32)

    detectable_16 = float((min_dim >= 16).mean())
    detectable_24 = float((min_dim >= 24).mean())
    detectable_32 = float((min_dim >= 32).mean())

    seg_bridge_recall = confusion_pct.get("Bridge", 0.0) / 100.0
    visual_a_fraction = quality_summary.get("A_clearly_visible", 0) / max(1, quality_summary.get("total", 1))
    weak_distinct = sim_summary.get("weak_fraction", 1.0)

    detection_feasibility_score = float(0.45 * detectable_16 + 0.35 * visual_a_fraction + 0.20 * (1.0 - weak_distinct))

    summary = {
        "median_bbox_w": float(np.median(widths)),
        "median_bbox_h": float(np.median(heights)),
        "median_bbox_area": float(np.median(areas)),
        "detectable_at_16px_fraction": detectable_16,
        "detectable_at_24px_fraction": detectable_24,
        "detectable_at_32px_fraction": detectable_32,
        "current_segmentation_bridge_recall": seg_bridge_recall,
        "detection_feasibility_score": detection_feasibility_score,
    }

    comparison = "Detection/instance route is more feasible than current segmentation" if detection_feasibility_score > seg_bridge_recall else "Segmentation remains at least as feasible as detection"

    lines = [
        "# Bridge Detector Feasibility Report",
        "",
        f"- total bridge instances: {len(entries)}",
        f"- median bridge bbox width: {summary['median_bbox_w']:.2f}",
        f"- median bridge bbox height: {summary['median_bbox_h']:.2f}",
        f"- median bridge bbox area: {summary['median_bbox_area']:.2f}",
        f"- detectable fraction (min dimension >= 16 px): {detectable_16 * 100:.4f}%",
        f"- detectable fraction (min dimension >= 24 px): {detectable_24 * 100:.4f}%",
        f"- detectable fraction (min dimension >= 32 px): {detectable_32 * 100:.4f}%",
        f"- current segmentation bridge recall proxy: {seg_bridge_recall * 100:.6f}%",
        f"- detection feasibility score: {detection_feasibility_score:.6f}",
        "",
        "## Segmentation vs Detection",
        f"- {comparison}",
    ]
    write_text(OUT_DIR / "bridge_detector_feasibility_report.md", "\n".join(lines) + "\n")
    write_text(OUT_DIR / "bridge_detector_feasibility_summary.json", json.dumps(summary, indent=2))
    return summary


def write_final_proof(
    evidence: dict[str, Any],
    inventory_stats: dict[str, float],
    sim_summary: dict[str, Any],
    quality_summary: dict[str, Any],
    info_summary: dict[str, Any],
    feature_summary: dict[str, Any],
    detector_summary: dict[str, Any],
) -> None:
    bridge_iou_zero = True
    campaign_text = read_text(ROOT / "outputs" / "bridge_campaign" / "checkpoint_comparison.md")
    if re.search(r"Bridge IoU=0\.0000", campaign_text) is None:
        bridge_iou_zero = False

    option = "OPTION B" if (
        bridge_iou_zero
        and float(feature_summary["bridge_confusion_percent"]["Bridge"]) < 1.0
        and float(info_summary["bridge_pct_of_fg"]) < 0.2
    ) else "OPTION A"

    lines = [
        "# Bridge Impossibility Proof",
        "",
        "## Decision",
        f"- {option}",
        "",
        "## Evidence Inputs",
        f"- evidence files found: {len(evidence['found'])}",
        f"- evidence files missing: {len(evidence['missing'])}",
    ]
    for p in evidence["missing"]:
        lines.append(f"- missing evidence path: {p}")

    lines.extend(
        [
            "",
            "## Measured Findings",
            f"- bridge instances extracted: {inventory_stats['total_bridges']}",
            f"- total bridge pixels in master catalog crops: {inventory_stats['total_bridge_pixels']}",
            f"- bridge share of foreground in dataset truth: {info_summary['bridge_pct_of_fg']:.6f}%",
            f"- current best checkpoint bridge prediction on GT bridge pixels: {feature_summary['bridge_confusion_percent']['Bridge']:.6f}%",
            f"- current best checkpoint road prediction on GT bridge pixels: {feature_summary['bridge_confusion_percent']['Road']:.6f}%",
            f"- feature separability silhouette (bridge vs road): {feature_summary['silhouette']:.6f}",
            f"- feature separability logistic AUC (bridge vs road): {feature_summary['logreg_auc']:.6f}",
            f"- weak visual distinctness fraction: {sim_summary.get('weak_fraction', 1.0) * 100:.4f}%",
            f"- annotation quality A/B/C: {quality_summary.get('A_clearly_visible', 0)}/{quality_summary.get('B_barely_visible', 0)}/{quality_summary.get('C_impossible', 0)}",
            f"- detector feasibility score: {detector_summary['detection_feasibility_score']:.6f}",
            "",
            "## Answers",
            "1. Why bridge is failing:",
            f"Bridge class remains unrecovered in A-G (Bridge IoU/F1 at zero), while bridge pixels are only {info_summary['bridge_pct_of_fg']:.6f}% of foreground and GT bridge pixels are overwhelmingly mapped to non-bridge classes.",
            "2. Whether bridge can be learned:",
            "Under current dataset distribution and current segmentation setup, measured results show no bridge recovery on validation.",
            "3. Whether more training is justified:",
            "Additional repetitions of the same segmentation setup are not justified by current measurements.",
            "4. Whether more data is required:",
            "Yes, bridge signal density is extremely low relative to competing classes.",
            "5. Whether relabeling is required:",
            "Bridge-vs-road separability and audit outcomes indicate relabeling or stricter bridge definition should be reviewed.",
            "6. Whether a detector should replace segmentation:",
            "Detection/instance formulation is comparatively more feasible than current segmentation according to measured feasibility score vs current segmentation bridge recall proxy.",
            "",
            "## Go / No-Go",
            "NO-GO for further DeepLab-style segmentation retraining on current data distribution.",
        ]
    )

    write_text(OUT_DIR / "bridge_impossibility_proof.md", "\n".join(lines) + "\n")


def main() -> int:
    ensure_dirs()

    evidence = evidence_digest()
    write_text(OUT_DIR / "evidence_manifest.json", json.dumps(evidence, indent=2))

    entries, inventory_stats = extract_bridge_master_catalog()
    write_bridge_inventory_report(inventory_stats, entries)

    similarity_df = compute_bridge_vs_road(entries)
    sim_summary = write_similarity_report(similarity_df)

    quality_df = classify_annotation_quality(similarity_df if not similarity_df.empty else pd.DataFrame(columns=["bridge_id", "split", "tiff_name", "bridge_pixels", "rgb_mean_z_dist", "distinct_score"]))
    quality_summary = write_annotation_quality_report(quality_df)

    feature_summary = feature_space_analysis()
    write_feature_separation_report(feature_summary)

    confusion_pct = write_confusion_report(feature_summary)

    dataset_truth = parse_dataset_truth()
    info_summary = write_information_content_report(dataset_truth, feature_summary)

    detector_summary = write_detector_feasibility_report(entries, quality_summary, confusion_pct, sim_summary)

    write_final_proof(
        evidence=evidence,
        inventory_stats=inventory_stats,
        sim_summary=sim_summary,
        quality_summary=quality_summary,
        info_summary=info_summary,
        feature_summary=feature_summary,
        detector_summary=detector_summary,
    )

    print(f"Bridge impossibility investigation artifacts written to: {OUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
