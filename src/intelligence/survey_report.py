"""Unified survey intelligence — answers 'so what?' after segmentation."""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np

from src.intelligence.explainability import ExplainabilityReport, build_explainability_report
from src.intelligence.spatial_analysis import SpatialIntelligence, analyze_spatial_intelligence
from src.intelligence.survey_operations import build_field_verification_queue
from src.inference.village_stats import VillageReport


@dataclass
class SurveyIntelligenceReport:
    village_name: str
    timestamp: str
    pixel_size_m: float
    infrastructure: dict
    spatial_intelligence: dict
    explainability: dict
    field_verification: dict
    executive_summary: list[str]
    provenance: dict

    def to_dict(self) -> dict:
        return asdict(self)

    def save_json(self, path: str | Path) -> None:
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")


def build_survey_intelligence(
    mask: np.ndarray,
    pixel_size_m: float,
    village_name: str = "Survey Area",
    logits: np.ndarray | None = None,
    confidence_map: np.ndarray | None = None,
    provenance: dict | None = None,
) -> SurveyIntelligenceReport:
    """Combine village stats, spatial intelligence, and explainability into one report."""
    village = VillageReport.from_mask(
        mask,
        pixel_size_m=pixel_size_m,
        village_name=village_name,
        confidence_map=confidence_map,
    )
    spatial = analyze_spatial_intelligence(mask, pixel_size_m)
    explain = build_explainability_report(mask, logits=logits, confidence_map=confidence_map)
    field_ops = build_field_verification_queue(
        mask,
        pixel_size_m,
        confidence_map=confidence_map,
        logits=logits,
        spatial=spatial,
    )

    executive = [
        f"Village Accessibility Score: {field_ops.village_accessibility_score:.0f}/100",
    ]
    executive.extend(field_ops.top_field_priorities[:3])
    executive.extend([
        f"Total survey area: {village.total_area_ha:.2f} ha",
        f"Road network: ~{village.road.total_length_m:,.0f} m across {spatial.road_connected_components} segment(s)",
        f"Built-up: {village.builtup.n_buildings} structures; {spatial.builtup_road_access_pct:.0f}% within road access buffer",
        f"Water: {village.water.n_water_bodies} bodies covering {village.water.area_m2:,.0f} m²",
        f"Automated confidence: {explain.high_confidence_pct:.0f}% high-confidence; "
        f"{explain.review_required_pct:.0f}% flagged for review",
    ])
    executive.extend(spatial.recommendations[:2])

    return SurveyIntelligenceReport(
        village_name=village_name,
        timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
        pixel_size_m=pixel_size_m,
        infrastructure={
            "total_area_ha": village.total_area_ha,
            "road_length_m": village.road.total_length_m,
            "road_coverage_pct": village.road.coverage_pct,
            "n_buildings": village.builtup.n_buildings,
            "builtup_area_m2": village.builtup.area_m2,
            "n_water_bodies": village.water.n_water_bodies,
            "water_area_m2": village.water.area_m2,
            "n_rooftops": village.builtup.rooftop_count,
        },
        spatial_intelligence=spatial.to_dict(),
        explainability=explain.to_dict(),
        field_verification=field_ops.to_dict(),
        executive_summary=executive,
        provenance=provenance or {},
    )
