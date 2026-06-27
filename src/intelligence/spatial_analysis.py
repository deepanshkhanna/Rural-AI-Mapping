"""Spatial intelligence derived from segmentation masks — decision support for survey teams."""

from __future__ import annotations

from dataclasses import asdict, dataclass

import cv2
import numpy as np

_ROAD = 1
_BUILTUP = 3
_WATER = 4


@dataclass
class SpatialIntelligence:
    """Infrastructure connectivity and accessibility metrics from a prediction mask."""

    pixel_size_m: float
    road_total_length_m: float
    road_connected_components: int
    road_largest_component_pct: float
    builtup_clusters: int
    builtup_road_access_pct: float
    builtup_water_proximity_pct: float
    water_bodies: int
    water_total_area_m2: float
    settlement_fragmentation_index: float
    recommendations: list[str]

    def to_dict(self) -> dict:
        return asdict(self)


def _skeleton_length_m(road_bin: np.ndarray, pixel_size_m: float) -> float:
    if road_bin.sum() == 0:
        return 0.0
    try:
        from skimage.morphology import skeletonize

        skel = skeletonize(road_bin.astype(bool))
        return float(skel.sum()) * pixel_size_m
    except ImportError:
        return float(road_bin.sum()) * pixel_size_m / 3.0


def analyze_spatial_intelligence(mask: np.ndarray, pixel_size_m: float) -> SpatialIntelligence:
    """
    Compute connectivity, accessibility, and settlement intelligence from a class mask.

    Metrics are designed for Panchayati Raj / SVAMITVA survey decision support:
    road access to built-up areas, water proximity risk, network fragmentation.
    """
    h, w = mask.shape
    px_area = pixel_size_m * pixel_size_m

    road_bin = (mask == _ROAD).astype(np.uint8)
    bu_bin = (mask == _BUILTUP).astype(np.uint8)
    water_bin = (mask == _WATER).astype(np.uint8)

    # Road network
    n_road, labels_road, stats_road, _ = cv2.connectedComponentsWithStats(road_bin, connectivity=8)
    road_components = max(0, n_road - 1)
    road_px = int(road_bin.sum())
    largest_road = 0
    if road_components > 0:
        largest_road = max(stats_road[i, cv2.CC_STAT_AREA] for i in range(1, n_road))
    largest_road_pct = 100.0 * largest_road / max(road_px, 1)
    road_length_m = _skeleton_length_m(road_bin, pixel_size_m)

    # Built-up clusters
    n_bu, _, stats_bu, _ = cv2.connectedComponentsWithStats(bu_bin, connectivity=8)
    bu_clusters = sum(1 for i in range(1, n_bu) if stats_bu[i, cv2.CC_STAT_AREA] >= 200)
    bu_px = int(bu_bin.sum())
    avg_cluster_px = bu_px / max(bu_clusters, 1)
    fragmentation = bu_clusters / max(bu_px / 10000.0, 0.01)  # clusters per ~100x100 block

    # Road access: built-up within ~50m of road
    road_radius_px = max(1, int(round(50.0 / pixel_size_m)))
    k_road = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE, (2 * road_radius_px + 1, 2 * road_radius_px + 1)
    )
    road_near = cv2.dilate(road_bin, k_road)
    bu_near_road = int((bu_bin & road_near).sum())
    bu_road_access_pct = 100.0 * bu_near_road / max(bu_px, 1)

    # Water proximity: built-up within ~30m of water (flood/setback proxy)
    water_radius_px = max(1, int(round(30.0 / pixel_size_m)))
    k_water = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE, (2 * water_radius_px + 1, 2 * water_radius_px + 1)
    )
    water_near = cv2.dilate(water_bin, k_water)
    bu_near_water = int((bu_bin & water_near).sum())
    bu_water_proximity_pct = 100.0 * bu_near_water / max(bu_px, 1)

    # Water inventory
    n_water, _, stats_water, _ = cv2.connectedComponentsWithStats(water_bin, connectivity=8)
    water_bodies = sum(1 for i in range(1, n_water) if stats_water[i, cv2.CC_STAT_AREA] >= 500)
    water_area_m2 = round(water_px * px_area, 1) if (water_px := int(water_bin.sum())) else 0.0

    recommendations: list[str] = []
    if road_components > 5 and largest_road_pct < 60:
        recommendations.append(
            f"Road network is fragmented ({road_components} segments; largest covers "
            f"{largest_road_pct:.0f}% of road pixels). Prioritize connectivity gaps for survey."
        )
    if bu_road_access_pct < 70 and bu_px > 0:
        recommendations.append(
            f"Only {bu_road_access_pct:.0f}% of built-up area is within ~50 m of mapped roads. "
            "Field verification recommended for remote settlements."
        )
    if bu_water_proximity_pct > 15 and bu_px > 0:
        recommendations.append(
            f"{bu_water_proximity_pct:.0f}% of built-up area is within ~30 m of water bodies. "
            "Review setback compliance and flood exposure."
        )
    if bu_clusters > 0 and fragmentation > 8:
        recommendations.append(
            f"Settlement appears dispersed ({bu_clusters} built-up clusters). "
            "Consider cluster-based property mapping workflow."
        )
    if not recommendations:
        recommendations.append(
            "Infrastructure layout appears coherent. Proceed with automated mapping; "
            "spot-check low-confidence zones flagged in explainability report."
        )

    return SpatialIntelligence(
        pixel_size_m=pixel_size_m,
        road_total_length_m=round(road_length_m, 1),
        road_connected_components=road_components,
        road_largest_component_pct=round(largest_road_pct, 1),
        builtup_clusters=bu_clusters,
        builtup_road_access_pct=round(bu_road_access_pct, 1),
        builtup_water_proximity_pct=round(bu_water_proximity_pct, 1),
        water_bodies=water_bodies,
        water_total_area_m2=water_area_m2,
        settlement_fragmentation_index=round(fragmentation, 2),
        recommendations=recommendations,
    )
