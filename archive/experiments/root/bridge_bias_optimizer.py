"""Memory-safe bridge bias optimization on cached logits.

Optimizes class-2 (Bridge) logit bias with chunked evaluation to avoid OOM.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

CACHE_DIR = Path("outputs/bias_cache")
OPT_BIAS_PATH = Path("outputs/optimal_bias.json")
OUT_PATH = Path("outputs/recovery_reports/bridge_bias_optimization_report.md")


def iter_chunks(arr: np.ndarray, chunk_size: int = 5_000_000):
    n = arr.shape[0]
    for i in range(0, n, chunk_size):
        yield arr[i : i + chunk_size]


def evaluate_bridge_multi_bias(logits: np.ndarray, gt: np.ndarray, b2_values: list[float], base_bias: np.ndarray) -> list[dict]:
    """Evaluate bridge metrics for many class-2 biases in one pass.

    Uses margin form:
      predict bridge iff (logit2 + b2) >= max(logit_other + bias_other)
    """
    b2_values = [float(v) for v in b2_values]
    stats = {b2: {"tp": 0, "fp": 0, "fn": 0} for b2 in b2_values}

    base_other = np.array([base_bias[0], base_bias[1], base_bias[3], base_bias[4]], dtype=np.float32)

    for lg, y in zip(iter_chunks(logits), iter_chunks(gt)):
        x = lg.astype(np.float32)
        bridge_logits = x[:, 2]
        other_logits = np.stack([x[:, 0], x[:, 1], x[:, 3], x[:, 4]], axis=1)
        other_max = (other_logits + base_other[None, :]).max(axis=1)

        t_bridge = y == 2
        for b2 in b2_values:
            p_bridge = (bridge_logits + b2) >= other_max
            tp_c = int((t_bridge & p_bridge).sum())
            fp_c = int((~t_bridge & p_bridge).sum())
            fn_c = int((t_bridge & ~p_bridge).sum())
            s = stats[b2]
            s["tp"] += tp_c
            s["fp"] += fp_c
            s["fn"] += fn_c

    rows = []
    for b2 in b2_values:
        s = stats[b2]
        tp, fp, fn = s["tp"], s["fp"], s["fn"]
        prec = tp / (tp + fp + 1e-10)
        rec = tp / (tp + fn + 1e-10)
        f1 = 2 * prec * rec / (prec + rec + 1e-10)
        iou = tp / (tp + fp + fn + 1e-10)
        rows.append(
            {
                "bridge_bias": float(b2),
                "bridge_iou": float(iou),
                "bridge_precision": float(prec),
                "bridge_recall": float(rec),
                "bridge_f1": float(f1),
                "tp": int(tp),
                "fp": int(fp),
                "fn": int(fn),
            }
        )
    return rows


def main() -> int:
    logits_path = CACHE_DIR / "ensemble_logits.npy"
    gt_path = CACHE_DIR / "gt_flat.npy"
    if not logits_path.exists() or not gt_path.exists():
        raise FileNotFoundError("Missing bias cache files. Run bias_search.py first.")

    logits = np.load(logits_path, mmap_mode="r")
    gt = np.load(gt_path, mmap_mode="r")

    if OPT_BIAS_PATH.exists():
        data = json.loads(OPT_BIAS_PATH.read_text(encoding="utf-8"))
        base_bias = np.array(data.get("optimal_bias", [0.0, 0.5, 2.0, 0.5, -0.5]), dtype=np.float32)
    else:
        base_bias = np.array([0.0, 0.5, 2.0, 0.5, -0.5], dtype=np.float32)

    grid = list(np.arange(0.0, 8.5, 0.5))
    rows = evaluate_bridge_multi_bias(logits, gt, grid, base_bias)
    best = max(rows, key=lambda x: (x["bridge_f1"], x["bridge_iou"]))
    trial_best = base_bias.copy()
    trial_best[2] = float(best["bridge_bias"])
    best["bias_vec"] = trial_best.tolist()

    # Persist optimized bias if it improves bridge F1.
    baseline = next((r for r in rows if abs(r["bridge_bias"] - float(base_bias[2])) < 1e-9), None)
    if baseline is None:
        baseline = evaluate_bridge_multi_bias(logits, gt, [float(base_bias[2])], base_bias)[0]
    improved = best is not None and best["bridge_f1"] > baseline["bridge_f1"] + 1e-9

    if improved:
        payload = {
            "optimal_bias": best["bias_vec"],
            "best_miou": None,
            "bridge_optimized": True,
            "bridge_metrics": {
                "baseline": baseline,
                "optimized": {
                    k: v
                    for k, v in best.items()
                    if k in {"bridge_iou", "bridge_precision", "bridge_recall", "bridge_f1", "tp", "fp", "fn", "bridge_bias"}
                },
            },
        }
        OPT_BIAS_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Bridge Bias Optimization Report",
        f"- baseline bridge F1: {baseline['bridge_f1']:.6f}",
        f"- baseline bridge IoU: {baseline['bridge_iou']:.6f}",
        f"- best bridge bias (class2): {best['bridge_bias']:.2f}",
        f"- optimized bridge F1: {best['bridge_f1']:.6f}",
        f"- optimized bridge IoU: {best['bridge_iou']:.6f}",
        f"- optimized TP/FP/FN: {best['tp']}/{best['fp']}/{best['fn']}",
        f"- applied_to_optimal_bias_json: {improved}",
        "",
        "## Grid Results",
    ]
    for r in rows:
        lines.append(
            f"- b2={r['bridge_bias']:.2f} | IoU={r['bridge_iou']:.6f} | F1={r['bridge_f1']:.6f} | "
            f"P={r['bridge_precision']:.6f} | R={r['bridge_recall']:.6f}"
        )

    OUT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUT_PATH}")
    print(f"Improved: {improved}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
