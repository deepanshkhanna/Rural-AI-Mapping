"""Field verification operations — ranked visit queue from mask + confidence (no ML)."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal

import cv2
import numpy as np

from src.intelligence.explainability import build_explainability_report, logits_to_confidence
from src.intelligence.spatial_analysis import SpatialIntelligence, analyze_spatial_intelligence

_ROAD = 1
_BUILTUP = 3
_WATER = 4

ROAD_ACCESS_M = 50.0
WATER_PROXIMITY_M = 30.0
MIN_CLUSTER_PX = 200
MIN_REVIEW_ZONE_PX = 500
CONFIDENCE_THRESHOLD = 0.70
DEDUP_DISTANCE_M = 30.0

WEIGHTS = {
    "confidence_risk": 0.35,
    "isolation_risk": 0.30,
    "cluster_size": 0.20,
    "water_proximity": 0.10,
    "fragmentation_context": 0.05,
}


@dataclass
class ScoreBreakdown:
    confidence_risk: float
    isolation_risk: float
    cluster_size: float
    water_proximity: float
    fragmentation_context: float
    weights: dict[str, float]

    def weighted_total(self) -> float:
        return (
            WEIGHTS["confidence_risk"] * self.confidence_risk
            + WEIGHTS["isolation_risk"] * self.isolation_risk
            + WEIGHTS["cluster_size"] * self.cluster_size
            + WEIGHTS["water_proximity"] * self.water_proximity
            + WEIGHTS["fragmentation_context"] * self.fragmentation_context
        )

    def to_dict(self) -> dict:
        d = asdict(self)
        d["weighted_total"] = round(self.weighted_total(), 2)
        return d


@dataclass
class FieldVisitItem:
    rank: int
    score: float
    centroid_x_px: float
    centroid_y_px: float
    item_type: Literal["settlement_cluster", "uncertain_zone"]
    label: str
    reason: str
    settlement_area_m2: float
    n_structures_estimate: int
    mean_confidence: float
    access_assessment: Literal["isolated", "partial", "connected", "n/a"]
    score_breakdown: dict

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class FieldVerificationResult:
    village_accessibility_score: float
    field_verification_queue: list[FieldVisitItem]
    top_field_priorities: list[str]
    scoring_model: dict

    def to_dict(self) -> dict:
        return {
            "village_accessibility_score": self.village_accessibility_score,
            "field_verification_queue": [q.to_dict() for q in self.field_verification_queue],
            "top_field_priorities": self.top_field_priorities,
            "scoring_model": self.scoring_model,
        }


def compute_village_accessibility_score(spatial: SpatialIntelligence) -> float:
    """Village-wide accessibility index 0–100 from spatial intelligence metrics."""
    access = spatial.builtup_road_access_pct / 100.0
    connectivity = spatial.road_largest_component_pct / 100.0
    frag_penalty = min(spatial.settlement_fragmentation_index / 10.0, 1.0)
    score = 100.0 * (0.40 * access + 0.30 * connectivity + 0.30 * (1.0 - frag_penalty))
    return round(float(np.clip(score, 0.0, 100.0)), 1)


def _road_near_mask(road_bin: np.ndarray, pixel_size_m: float) -> np.ndarray:
    radius_px = max(1, int(round(ROAD_ACCESS_M / pixel_size_m)))
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * radius_px + 1, 2 * radius_px + 1))
    return cv2.dilate(road_bin, k)


def _water_near_mask(water_bin: np.ndarray, pixel_size_m: float) -> np.ndarray:
    radius_px = max(1, int(round(WATER_PROXIMITY_M / pixel_size_m)))
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * radius_px + 1, 2 * radius_px + 1))
    return cv2.dilate(water_bin, k)


def _access_label(road_access_pct: float, is_builtup: bool) -> str:
    if not is_builtup:
        return "n/a"
    if road_access_pct <= 0.0:
        return "isolated"
    if road_access_pct < 70.0:
        return "partial"
    return "connected"


def _score_candidate(
    mean_confidence: float,
    road_access_pct: float,
    area_m2: float,
    water_proximity_pct: float,
    fragmentation_index: float,
    is_builtup: bool,
) -> ScoreBreakdown:
    confidence_risk = float(np.clip((1.0 - mean_confidence) * 100.0, 0.0, 100.0))
    if is_builtup:
        isolation_risk = 100.0 if road_access_pct <= 0.0 else float(np.clip(100.0 - road_access_pct, 0.0, 100.0))
    else:
        isolation_risk = float(np.clip(confidence_risk * 0.6, 0.0, 100.0))
    cluster_size = float(np.clip(np.sqrt(max(area_m2, 1.0)) * 4.0, 0.0, 100.0))
    water_prox = float(np.clip(water_proximity_pct, 0.0, 100.0))
    frag_ctx = float(np.clip(min(fragmentation_index * 10.0, 100.0), 0.0, 100.0))
    return ScoreBreakdown(
        confidence_risk=round(confidence_risk, 2),
        isolation_risk=round(isolation_risk, 2),
        cluster_size=round(cluster_size, 2),
        water_proximity=round(water_prox, 2),
        fragmentation_context=round(frag_ctx, 2),
        weights=dict(WEIGHTS),
    )


def _reason_from_breakdown(
    label: str,
    breakdown: ScoreBreakdown,
    access: str,
    item_type: str,
) -> str:
    parts: list[str] = []
    if breakdown.isolation_risk >= 70:
        parts.append("poor road access" if access != "n/a" else "low-confidence region")
    elif access == "isolated":
        parts.append("isolated from road network")
    if breakdown.confidence_risk >= 50:
        parts.append("low model confidence")
    if breakdown.cluster_size >= 40:
        parts.append("large settlement footprint")
    if breakdown.water_proximity >= 30:
        parts.append("near water body (setback review)")
    if breakdown.fragmentation_context >= 40:
        parts.append("dispersed settlement context")
    if not parts:
        if item_type == "uncertain_zone":
            parts.append("model uncertainty requires field confirmation")
        else:
            parts.append("routine verification recommended")
    detail = ", ".join(parts)
    return f"{label}: {detail}"


def _estimate_structures(area_px: int, px_area: float) -> int:
    avg_building_m2 = 80.0
    return max(1, int(round((area_px * px_area) / avg_building_m2))) if area_px > 0 else 0


def build_field_verification_queue(
    mask: np.ndarray,
    pixel_size_m: float,
    confidence_map: np.ndarray | None = None,
    logits: np.ndarray | None = None,
    spatial: SpatialIntelligence | None = None,
    max_items: int = 10,
) -> FieldVerificationResult:
    """
    Build ranked field visit queue from segmentation outputs.

    Deterministic: same inputs → same ranking.
    """
    if confidence_map is None:
        if logits is not None:
            confidence_map = logits_to_confidence(logits)
        else:
            confidence_map = np.full(mask.shape, 0.5, dtype=np.float32)

    if spatial is None:
        spatial = analyze_spatial_intelligence(mask, pixel_size_m)

    px_area = pixel_size_m * pixel_size_m
    h, w = mask.shape
    road_bin = (mask == _ROAD).astype(np.uint8)
    bu_bin = (mask == _BUILTUP).astype(np.uint8)
    water_bin = (mask == _WATER).astype(np.uint8)
    road_near = _road_near_mask(road_bin, pixel_size_m)
    water_near = _water_near_mask(water_bin, pixel_size_m)

    candidates: list[dict] = []

    # Built-up settlement clusters
    n_bu, labels_bu, stats_bu, centroids_bu = cv2.connectedComponentsWithStats(bu_bin, connectivity=8)
    cluster_idx = 0
    for i in range(1, n_bu):
        area_px = int(stats_bu[i, cv2.CC_STAT_AREA])
        if area_px < MIN_CLUSTER_PX:
            continue
        cluster_idx += 1
        region = labels_bu == i
        mean_conf = float(confidence_map[region].mean())
        bu_in_region = region
        road_access_pct = 100.0 * (bu_in_region & road_near.astype(bool)).sum() / max(area_px, 1)
        water_pct = 100.0 * (bu_in_region & water_near.astype(bool)).sum() / max(area_px, 1)
        area_m2 = area_px * px_area
        cx, cy = centroids_bu[i]
        breakdown = _score_candidate(
            mean_conf, road_access_pct, area_m2, water_pct,
            spatial.settlement_fragmentation_index, is_builtup=True,
        )
        score = float(np.clip(breakdown.weighted_total(), 0.0, 100.0))
        access = _access_label(road_access_pct, True)
        label = f"Settlement Cluster {cluster_idx}"
        candidates.append({
            "score": score,
            "cx": float(cx),
            "cy": float(cy),
            "item_type": "settlement_cluster",
            "label": label,
            "area_m2": area_m2,
            "area_px": area_px,
            "n_structures": _estimate_structures(area_px, px_area),
            "mean_conf": mean_conf,
            "access": access,
            "breakdown": breakdown,
        })

    # Low-confidence review zones
    explain = build_explainability_report(mask, confidence_map=confidence_map)
    zone_idx = 0
    uncertain_bin = (confidence_map < CONFIDENCE_THRESHOLD).astype(np.uint8)
    n_u, labels_u, stats_u, centroids_u = cv2.connectedComponentsWithStats(uncertain_bin, connectivity=8)
    for i in range(1, n_u):
        area_px = int(stats_u[i, cv2.CC_STAT_AREA])
        if area_px < MIN_REVIEW_ZONE_PX:
            continue
        region = labels_u == i
        bu_overlap = int((region & bu_bin.astype(bool)).sum())
        if bu_overlap > 0.5 * area_px:
            continue
        zone_idx += 1
        mean_conf = float(confidence_map[region].mean())
        area_m2 = area_px * px_area
        water_pct = 100.0 * (region & water_near.astype(bool)).sum() / max(area_px, 1)
        breakdown = _score_candidate(
            mean_conf, 0.0, area_m2, water_pct,
            spatial.settlement_fragmentation_index, is_builtup=False,
        )
        score = float(np.clip(breakdown.weighted_total(), 0.0, 100.0))
        label = f"Uncertain Zone {zone_idx}"
        candidates.append({
            "score": score,
            "cx": float(centroids_u[i][0]),
            "cy": float(centroids_u[i][1]),
            "item_type": "uncertain_zone",
            "label": label,
            "area_m2": area_m2,
            "area_px": area_px,
            "n_structures": 0,
            "mean_conf": mean_conf,
            "access": "n/a",
            "breakdown": breakdown,
        })

    dedup_px = max(1, int(round(DEDUP_DISTANCE_M / pixel_size_m)))
    dedup_r2 = dedup_px * dedup_px
    candidates.sort(key=lambda c: c["score"], reverse=True)
    filtered: list[dict] = []
    for c in candidates:
        if any((c["cx"] - f["cx"]) ** 2 + (c["cy"] - f["cy"]) ** 2 < dedup_r2 for f in filtered):
            continue
        filtered.append(c)
        if len(filtered) >= max_items:
            break

    queue: list[FieldVisitItem] = []
    for rank, c in enumerate(filtered, start=1):
        bd: ScoreBreakdown = c["breakdown"]
        reason = _reason_from_breakdown(c["label"], bd, c["access"], c["item_type"])
        queue.append(
            FieldVisitItem(
                rank=rank,
                score=round(c["score"], 1),
                centroid_x_px=round(c["cx"], 1),
                centroid_y_px=round(c["cy"], 1),
                item_type=c["item_type"],
                label=c["label"],
                reason=reason,
                settlement_area_m2=round(c["area_m2"], 1),
                n_structures_estimate=c["n_structures"],
                mean_confidence=round(c["mean_conf"], 4),
                access_assessment=c["access"],
                score_breakdown=bd.to_dict(),
            )
        )

    accessibility = compute_village_accessibility_score(spatial)
    top_priorities = _top_priority_lines(queue, max_n=3)

    return FieldVerificationResult(
        village_accessibility_score=accessibility,
        field_verification_queue=queue,
        top_field_priorities=top_priorities,
        scoring_model={
            "name": "SurveyPriorityScore",
            "range": "0-100",
            "weights": WEIGHTS,
            "road_access_buffer_m": ROAD_ACCESS_M,
            "water_proximity_buffer_m": WATER_PROXIMITY_M,
            "confidence_threshold": CONFIDENCE_THRESHOLD,
        },
    )


def _top_priority_lines(queue: list[FieldVisitItem], max_n: int = 3) -> list[str]:
    lines: list[str] = []
    for item in queue[:max_n]:
        if item.item_type == "settlement_cluster":
            if item.access_assessment == "isolated":
                action = f"Verify isolated {item.label.lower()} (no road within {ROAD_ACCESS_M:.0f} m)"
            elif item.mean_confidence < CONFIDENCE_THRESHOLD:
                action = f"Inspect low-confidence {item.label.lower()}"
            else:
                action = f"Field-verify {item.label.lower()} ({item.settlement_area_m2:.0f} m²)"
        else:
            action = f"Confirm classification in {item.label.lower()} (model uncertain)"
        lines.append(f"Priority #{item.rank}: {action}")
    if not lines:
        lines.append("Priority #1: No high-risk zones detected — proceed with spot-check of low-confidence pixels")
    return lines


def render_field_verification_overlay(
    base_rgb: np.ndarray,
    queue: list[FieldVisitItem] | list[dict],
    max_markers: int = 5,
) -> np.ndarray:
    """Draw numbered priority markers on RGB image. Rank 1 = highest priority."""
    out = base_rgb.copy()
    if out.ndim == 2:
        out = cv2.cvtColor(out, cv2.COLOR_GRAY2RGB)
    if not queue:
        cv2.putText(
            out, "No field priorities", (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 200, 80), 2, cv2.LINE_AA,
        )
        return out

    colors = [
        (255, 60, 60),
        (255, 140, 60),
        (255, 220, 80),
        (180, 220, 100),
        (120, 200, 120),
    ]
    items = queue[:max_markers]
    for i, raw in enumerate(items):
        if isinstance(raw, FieldVisitItem):
            cx, cy, rank = int(raw.centroid_x_px), int(raw.centroid_y_px), raw.rank
        else:
            cx, cy, rank = int(raw["centroid_x_px"]), int(raw["centroid_y_px"]), raw["rank"]
        cx = int(np.clip(cx, 0, out.shape[1] - 1))
        cy = int(np.clip(cy, 0, out.shape[0] - 1))
        color = colors[min(i, len(colors) - 1)]
        cv2.circle(out, (cx, cy), 18, color, -1, lineType=cv2.LINE_AA)
        cv2.circle(out, (cx, cy), 18, (255, 255, 255), 2, lineType=cv2.LINE_AA)
        cv2.putText(
            out, str(rank), (cx - 8, cy + 6),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2, cv2.LINE_AA,
        )

    cv2.putText(
        out, "Field visit priority (1 = go first)", (10, out.shape[0] - 12),
        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (230, 230, 230), 1, cv2.LINE_AA,
    )
    return out
