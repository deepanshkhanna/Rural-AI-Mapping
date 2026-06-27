"""Explainability utilities — confidence analysis and review-zone identification."""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np

CLASS_NAMES = {
    0: "Background",
    1: "Road",
    2: "Bridge",
    3: "Built-Up Area",
    4: "Water Body",
}


@dataclass
class ExplainabilityReport:
    confidence_threshold: float
    high_confidence_pct: float
    review_required_pct: float
    per_class_mean_confidence: dict[str, float]
    uncertain_pixel_count: int
    review_zones: list[dict]
    audit_notes: list[str]

    def to_dict(self) -> dict:
        return asdict(self)


def logits_to_confidence(logits: np.ndarray) -> np.ndarray:
    """(C, H, W) logits → (H, W) max softmax confidence."""
    shifted = logits - logits.max(axis=0, keepdims=True)
    exp = np.exp(shifted)
    probs = exp / (exp.sum(axis=0, keepdims=True) + 1e-9)
    return probs.max(axis=0).astype(np.float32)


def build_explainability_report(
    mask: np.ndarray,
    logits: np.ndarray | None = None,
    confidence_map: np.ndarray | None = None,
    threshold: float = 0.70,
    min_review_zone_px: int = 500,
) -> ExplainabilityReport:
    """
    Build judge-inspectable explainability summary.

    Either logits (C,H,W) or confidence_map (H,W) must be provided.
    """
    if confidence_map is None:
        if logits is None:
            raise ValueError("Provide logits or confidence_map")
        confidence_map = logits_to_confidence(logits)

    h, w = mask.shape
    high_conf = float((confidence_map >= threshold).mean() * 100.0)
    review_pct = 100.0 - high_conf
    uncertain_px = int((confidence_map < threshold).sum())

    per_class: dict[str, float] = {}
    for cid, name in CLASS_NAMES.items():
        region = mask == cid
        if region.any():
            per_class[name] = round(float(confidence_map[region].mean()), 4)
        else:
            per_class[name] = 0.0

    # Identify contiguous low-confidence zones for field review
    import cv2

    uncertain_bin = (confidence_map < threshold).astype(np.uint8)
    n_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(uncertain_bin, connectivity=8)
    review_zones: list[dict] = []
    for i in range(1, n_labels):
        area = stats[i, cv2.CC_STAT_AREA]
        if area < min_review_zone_px:
            continue
        cx, cy = centroids[i]
        review_zones.append({
            "zone_id": len(review_zones) + 1,
            "centroid_x_px": round(float(cx), 1),
            "centroid_y_px": round(float(cy), 1),
            "area_px": int(area),
            "mean_confidence": round(float(confidence_map[labels == i].mean()), 4),
        })
    review_zones.sort(key=lambda z: z["area_px"], reverse=True)
    review_zones = review_zones[:10]

    notes = [
        f"Pixels above {threshold:.0%} confidence: {high_conf:.1f}%",
        f"Field review recommended for {len(review_zones)} contiguous uncertain zone(s)",
        "Per-class confidence is mean softmax probability within predicted class regions",
    ]

    return ExplainabilityReport(
        confidence_threshold=threshold,
        high_confidence_pct=round(high_conf, 2),
        review_required_pct=round(review_pct, 2),
        per_class_mean_confidence=per_class,
        uncertain_pixel_count=uncertain_px,
        review_zones=review_zones,
        audit_notes=notes,
    )
