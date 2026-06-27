#!/usr/bin/env python3
"""Production certification — one candidate per process to limit memory."""
from __future__ import annotations
import argparse, gc, json, subprocess, sys, time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import torch
from torch.utils.data import DataLoader
from tqdm import tqdm

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from bias_search import load_model_from_ckpt
from run_calibrated_eval import run_eval
from src.config.platform_config import load_platform_config
from src.datasets.unified_dataset import CLASS_NAMES, UnifiedMultiClassDataset, get_default_sources, get_val_transform
from src.evaluation.unified_evaluator import compute_counts_metrics
from src.inference.calibrated_engine import CalibratedEngine
from src.security.checkpoints import file_sha256, load_checkpoint_secure

PLATFORM_CFG = load_platform_config()
NUM_CLASSES = PLATFORM_CFG.num_classes
VAL_TIFFS = list(PLATFORM_CFG.val_tiffs)
TRAIN_TIFFS = list(PLATFORM_CFG.train_tiffs)
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
BATCH_SIZE = 4
NUM_WORKERS = 2
W_BEST, W_LATEST = 0.65, 0.35
OUT_DIR = ROOT / "outputs/certification"
BIAS_DIR = OUT_DIR / "bias"
RESULTS_JSON = OUT_DIR / "certification_results.json"
LATEST = ROOT / "outputs/checkpoints/latest_model.pth"
CANDIDATES = {
    "epoch_33": {"best": ROOT / "outputs/checkpoints_backup/timed/checkpoint_20260615_2104.pth", "latest": LATEST},
    "epoch_69": {"best": ROOT / "outputs/checkpoints_backup/timed/checkpoint_20260615_2131.pth", "latest": LATEST},
    "epoch_71": {"best": ROOT / "outputs/checkpoints/best_model.pth", "latest": LATEST},
    "epoch_80": {"best": LATEST, "latest": LATEST},
}

@dataclass
class CkptRecord:
    path: str; epoch: int|None; encoder: str; architecture: str; experiment: str
    params: int; size_mb: float; mtime: str; sha256: str; viable: bool; notes: str

def inventory():
    out = []
    for p in sorted(ROOT.rglob("*.pth")):
        if ".venv" in p.parts or "production_release" in p.parts: continue
        try:
            ck = load_checkpoint_secure(p, map_location="cpu")
            cfg = ck.get("config") or {}
            enc = cfg.get("encoder_name", "?")
            sd = ck.get("model_state_dict") or ck.get("ema_state_dict") or {}
            params = sum(v.numel() for v in sd.values()) if sd else 0
            out.append(CkptRecord(str(p.relative_to(ROOT)), ck.get("epoch"), enc, cfg.get("architecture","?"), cfg.get("experiment_name","?"), params, round(p.stat().st_size/1048576,2), datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc).isoformat(), file_sha256(p), enc=="resnet50" and params>1e6, "legacy resnet18" if enc=="resnet18" else ""))
        except Exception as e:
            out.append(CkptRecord(str(p.relative_to(ROOT)), None, "?", "?", "?", 0, round(p.stat().st_size/1048576,2), "", "", False, str(e)))
    return out

def val_loader(cfg, tiffs=None):
    ds = UnifiedMultiClassDataset(sources=get_default_sources(), split="val", transform=get_val_transform(cfg.get("image_size",768)), patch_size=cfg.get("image_size",768), patches_per_image=cfg.get("patches_per_image",50), train_tiffs=TRAIN_TIFFS, val_tiffs=tiffs or VAL_TIFFS)
    return DataLoader(ds, batch_size=BATCH_SIZE, shuffle=False, num_workers=NUM_WORKERS, pin_memory=True)

def cache_logits(best_p, latest_p, cache_dir, loader):
    cache_dir.mkdir(parents=True, exist_ok=True)
    lc, gc_ = cache_dir/"ensemble_logits.npy", cache_dir/"gt_flat.npy"
    if lc.exists() and gc_.exists():
        return np.load(lc, mmap_mode="r"), np.load(gc_, mmap_mode="r")
    mb, _ = load_model_from_ckpt(best_p, "model_state_dict")
    ml, _ = load_model_from_ckpt(latest_p, "ema_state_dict")
    mb.eval(); ml.eval()
    al, ag = [], []
    with torch.no_grad():
        for images, masks in tqdm(loader, desc=cache_dir.name):
            images = images.to(DEVICE, non_blocking=True)
            with torch.amp.autocast(device_type="cuda", enabled=DEVICE=="cuda"):
                lb, ll = mb(images).float(), ml(images).float()
            ens = W_BEST*lb + W_LATEST*ll
            b,c,h,w = ens.shape
            al.append(ens.cpu().numpy().transpose(0,2,3,1).reshape(-1,c).astype(np.float16))
            ag.append(masks.numpy().reshape(-1).astype(np.uint8))
    del mb, ml; torch.cuda.empty_cache() if DEVICE=="cuda" else None; gc.collect()
    la, ga = np.concatenate(al), np.concatenate(ag)
    np.save(lc, la); np.save(gc_, ga)
    return la, ga

def apply_bias_and_iou_chunked(logits_f16: np.ndarray, gt: np.ndarray, bias: np.ndarray, chunk: int = 2_000_000):
    """Memory-safe bias IoU for large logit caches."""
    bias = bias.astype(np.float32)
    inter = np.zeros(NUM_CLASSES, dtype=np.int64)
    union = np.zeros(NUM_CLASSES, dtype=np.int64)
    n = len(gt)
    for start in range(0, n, chunk):
        end = min(start + chunk, n)
        biased = logits_f16[start:end].astype(np.float32) + bias
        preds = biased.argmax(axis=1).astype(np.uint8)
        g = gt[start:end]
        for c in range(1, NUM_CLASSES):
            gt_c = g == c
            if not gt_c.any():
                continue
            pr_c = preds == c
            inter[c] += int((gt_c & pr_c).sum())
            union[c] += int((gt_c | pr_c).sum())
    fg = {c: float(inter[c]) / float(union[c] + 1e-10) for c in range(1, NUM_CLASSES) if union[c] > 0}
    miou = float(np.mean(list(fg.values()))) if fg else 0.0
    return miou, fg


def coordinate_descent_chunked(logits: np.ndarray, gt: np.ndarray) -> tuple[np.ndarray, float]:
    grids = {
        0: np.array([-2.0, -1.0, -0.5, 0.0]),
        1: np.arange(0.0, 3.5, 0.25),
        2: np.arange(0.0, 6.5, 0.5),
        3: np.array([-0.5, -0.25, 0.0, 0.25, 0.5]),
        4: np.array([-0.5, 0.0, 0.5]),
    }
    best_bias = np.zeros(NUM_CLASSES, dtype=np.float32)
    best_miou, _ = apply_bias_and_iou_chunked(logits, gt, best_bias)
    print(f"Baseline FG mIoU (bias=0): {best_miou:.4f}")
    for _round in range(3):
        changed = False
        for c in range(NUM_CLASSES):
            best_c = best_bias[c]
            for val in grids[c]:
                trial = best_bias.copy()
                trial[c] = float(val)
                miou_t, _ = apply_bias_and_iou_chunked(logits, gt, trial)
                if miou_t > best_miou + 1e-5:
                    best_miou = miou_t
                    best_bias = trial.copy()
                    best_c = float(val)
                    changed = True
            best_bias[c] = best_c
        if not changed:
            break
    print(f"Optimised FG mIoU: {best_miou:.4f}")
    return best_bias, best_miou


def run_bias(name, best_p, latest_p, loader):
    logits, gt = cache_logits(best_p, latest_p, OUT_DIR / "bias_cache" / name, loader)
    bias, miou = coordinate_descent_chunked(logits, gt)
    _, per = apply_bias_and_iou_chunked(logits, gt, bias)
    payload = {"candidate":name,"optimal_bias":bias.tolist(),"best_miou":float(miou),"per_class_iou_bias_only":{CLASS_NAMES.get(c,str(c)):float(v) for c,v in per.items()},"ensemble_weights":{"best":W_BEST,"latest":W_LATEST},"best_ckpt":str(best_p.relative_to(ROOT)),"latest_ckpt":str(latest_p.relative_to(ROOT)),"generated_at":datetime.now(timezone.utc).isoformat()}
    bp = BIAS_DIR/f"optimal_bias_{name}.json"; BIAS_DIR.mkdir(parents=True, exist_ok=True)
    bp.write_text(json.dumps(payload, indent=2))
    return payload

def run_eval_cand(name, best_p, latest_p, bias_path, loader, tta=True):
    eng = CalibratedEngine.from_checkpoints(best_p, latest_p, device=DEVICE, bias_path=bias_path, use_tta=tta, require_bias_file=True)
    base = run_eval(eng, loader, postprocess=False)
    cal = run_eval(eng, loader, postprocess=True)
    del eng; torch.cuda.empty_cache() if DEVICE=="cuda" else None
    return {"candidate":name,"use_tta":tta,"baseline":base,"calibrated":cal}

def confusion(best_p, latest_p, bias_path, loader):
    eng = CalibratedEngine.from_checkpoints(best_p, latest_p, device=DEVICE, bias_path=bias_path, use_tta=True, require_bias_file=True)
    cm = np.zeros((NUM_CLASSES,NUM_CLASSES), dtype=np.int64)
    tp = np.zeros(NUM_CLASSES, dtype=np.int64)
    gt_px = np.zeros(NUM_CLASSES, dtype=np.int64)
    pr_px = np.zeros(NUM_CLASSES, dtype=np.int64)
    for images, masks in tqdm(loader, desc="Confusion"):
        preds, _ = eng.predict_batch(images, postprocess=True, strict_postprocess=True)
        for b in range(preds.shape[0]):
            t, p = masks.numpy()[b].flatten(), preds[b].flatten()
            for i in range(NUM_CLASSES):
                for j in range(NUM_CLASSES): cm[i,j] += int(((t==i)&(p==j)).sum())
            for c in range(NUM_CLASSES):
                tp[c]+=int(((t==c)&(p==c)).sum()); gt_px[c]+=int((t==c).sum()); pr_px[c]+=int((p==c).sum())
    del eng; torch.cuda.empty_cache() if DEVICE=="cuda" else None
    metrics = compute_counts_metrics(tp, gt_px, pr_px, CLASS_NAMES)
    pairs = []
    for gt_c in range(1, NUM_CLASSES):
        for pred_c in range(NUM_CLASSES):
            if gt_c==pred_c: continue
            cnt = int(cm[gt_c,pred_c])
            if cnt and gt_px[gt_c]: pairs.append({"gt":CLASS_NAMES[gt_c],"pred":CLASS_NAMES[pred_c],"pixels":cnt,"pct_of_gt":round(100*cnt/gt_px[gt_c],2)})
    pairs.sort(key=lambda x:x["pixels"], reverse=True)
    fnfp = {CLASS_NAMES[c]:{"false_negatives":int(gt_px[c]-tp[c]),"false_positives":int(pr_px[c]-tp[c]),"gt_pixels":int(gt_px[c]),"pred_pixels":int(pr_px[c])} for c in range(1,NUM_CLASSES)}
    return {"metrics":metrics,"confusion_matrix":cm.tolist(),"top_confusions":pairs[:12],"fn_fp":fnfp}

def load_res():
    return json.loads(RESULTS_JSON.read_text()) if RESULTS_JSON.exists() else {"generated_at":datetime.now(timezone.utc).isoformat(),"val_tiffs":VAL_TIFFS,"candidates":{}}

def _delete_cache(name: str) -> None:
    import shutil
    cache = OUT_DIR / "bias_cache" / name
    if cache.exists():
        shutil.rmtree(cache)
        print(f"Deleted cache: {cache}")


def run_candidate(name, stress=False):
    out_path = OUT_DIR / f"{name}_results.json"
    if out_path.exists() and not stress:
        print(f"SKIP {name}: {out_path} already exists")
        return

    best_p, latest_p = CANDIDATES[name]["best"], CANDIDATES[name]["latest"]
    cfg = load_checkpoint_secure(best_p, map_location="cpu")["config"]
    loader = val_loader(cfg)
    t0 = time.time()
    cand = {
        "candidate": name,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "val_patches": len(loader.dataset),
        "val_tiffs": VAL_TIFFS,
        "best_ckpt": str(best_p.relative_to(ROOT)),
        "latest_ckpt": str(latest_p.relative_to(ROOT)),
        "best_sha256": file_sha256(best_p),
        "latest_sha256": file_sha256(latest_p),
        "best_epoch": int(load_checkpoint_secure(best_p, map_location="cpu").get("epoch", -1)),
        "latest_epoch": int(load_checkpoint_secure(latest_p, map_location="cpu").get("epoch", -1)),
    }
    cand["bias"] = run_bias(name, best_p, latest_p, loader)
    bp = BIAS_DIR / f"optimal_bias_{name}.json"
    cand["eval_calibrated_tta"] = run_eval_cand(name, best_p, latest_p, bp, loader, True)
    cand["class_metrics"] = cand["eval_calibrated_tta"]["calibrated"]
    cand["summary"] = {
        "fg_miou": cand["class_metrics"]["fg_miou"],
        "road_iou": cand["class_metrics"]["Road"]["iou"],
        "builtup_iou": cand["class_metrics"]["Built-Up Area"]["iou"],
        "water_iou": cand["class_metrics"]["Water Body"]["iou"],
        "bridge_iou": cand["class_metrics"]["Bridge"]["iou"],
        "optimal_bias": cand["bias"]["optimal_bias"],
        "bias_search_fg_miou": cand["bias"]["best_miou"],
    }
    if stress:
        cand["eval_no_tta"] = run_eval_cand(name, best_p, latest_p, bp, loader, False)
        cand["per_village_tta"] = {
            t: run_eval_cand(name, best_p, latest_p, bp, val_loader(cfg, [t]), True)["calibrated"]
            for t in VAL_TIFFS
        }
    cand["elapsed_seconds"] = round(time.time() - t0, 1)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if stress and out_path.exists():
        prev = json.loads(out_path.read_text())
        prev.update({k: v for k, v in cand.items() if k.startswith("eval_") or k == "per_village_tta"})
        prev["stress_generated_at"] = cand["generated_at"]
        out_path.write_text(json.dumps(prev, indent=2))
    else:
        out_path.write_text(json.dumps(cand, indent=2))
    _delete_cache(name)
    gc.collect()
    if DEVICE == "cuda":
        torch.cuda.empty_cache()
    print(f"Wrote {out_path}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidate", choices=list(CANDIDATES))
    ap.add_argument("--inventory-only", action="store_true")
    ap.add_argument("--stress", action="store_true")
    a = ap.parse_args()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if a.inventory_only:
        (OUT_DIR/"checkpoint_inventory.json").write_text(json.dumps([r.__dict__ for r in inventory()], indent=2)); sys.exit(0)
    if not a.candidate: ap.error("--candidate required")
    run_candidate(a.candidate, a.stress); print("done", a.candidate)
