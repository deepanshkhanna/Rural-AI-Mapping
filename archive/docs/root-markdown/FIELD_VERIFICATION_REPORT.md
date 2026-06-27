# Field Verification Priority Queue — Implementation Report

## Executive Summary

This feature transforms segmentation outputs into an **actionable field verification worklist** for district survey officers. It answers: *"I only have one day and one field team — where should I go first?"*

Deliverables: deterministic `SurveyPriorityScore` (0–100), ranked `field_verification_queue[]`, Village Accessibility Score, numbered map overlay, judge-first HTML section, API/Streamlit/JSON integration, and 9 automated tests.

---

## Design Rationale

Most hackathon submissions stop at colored masks. SVAMITVA officers need **visit scheduling**, not another heatmap.

The queue combines two candidate types:

1. **Settlement clusters** — built-up connected components (≥ 200 px) where property verification matters.
2. **Uncertain zones** — low-confidence regions (confidence &lt; 0.70, ≥ 500 px) where the model needs human confirmation.

Each candidate receives an explainable `SurveyPriorityScore`. Officers see *why* a location ranks high (isolation, confidence, size, water proximity, fragmentation). Rankings deduplicate targets within 30 m so one field visit is not double-counted.

Full workflow: see [FIELD_VERIFICATION_DESIGN.md](FIELD_VERIFICATION_DESIGN.md).

---

## Formulas

### SurveyPriorityScore (per visit target, 0–100)

| Component | Weight | Formula |
|-----------|--------|---------|
| Confidence risk | 35% | `(1 − mean_confidence) × 100` |
| Isolation risk | 30% | Built-up: `100` if 0% within 50 m road buffer, else `100 − local_road_access%`. Uncertain zones: `confidence_risk × 0.6` |
| Cluster size | 20% | `min(100, √(area_m²) × 4)` |
| Water proximity | 10% | `% pixels within 30 m of water` |
| Fragmentation context | 5% | `min(100, settlement_fragmentation_index × 10)` |

**Total:** `clamp(Σ weightᵢ × componentᵢ, 0, 100)`

### Village Accessibility Score (village-wide, 0–100)

```
0.40 × builtup_road_access_pct
+ 0.30 × road_largest_component_pct
+ 0.30 × (1 − min(fragmentation_index / 10, 1)) × 100
```

---

## Files Changed

| File | Role |
|------|------|
| `src/intelligence/survey_operations.py` | Core scoring, queue builder, overlay renderer |
| `src/intelligence/survey_report.py` | Wires `field_verification` into `build_survey_intelligence()` |
| `src/intelligence/__init__.py` | Public exports |
| `scripts/generate_judge_package.py` | Full-raster survey + `07_field_priority_map.png` + HTML reorder |
| `production/api.py` | `/survey-report` returns `field_verification` via `report.to_dict()` |
| `demo_ui/app.py` | Field Verification Priorities expander (demo moment) |
| `demo_ui/pages/2_Judge_Verification.py` | Judge verification “three places tomorrow” screen |
| `tests/test_survey_operations.py` | 9 tests for ranking, stability, edge cases |
| `tests/test_intelligence.py` | Asserts `field_verification` in survey dict |
| `FIELD_VERIFICATION_DESIGN.md` | Phase 1 design review |
| `evidence/judge_package/index.html` | Field Verification Priorities **first** |
| `evidence/judge_package/survey_intelligence.json` | Sample JSON with queue |
| `evidence/judge_package/overlays/07_field_priority_map.png` | Numbered priority map |

---

## Screenshots Generated

| Artifact | Path |
|----------|------|
| Field priority map (numbered 1–3) | `evidence/judge_package/overlays/07_field_priority_map.png` |
| Judge HTML (priorities above metrics) | `evidence/judge_package/index.html` |

Regenerate:

```bash
SVAMITVA_CONFIG_PATH=config/platform_config.synthetic.json \
  .venv/bin/python scripts/generate_judge_package.py
```

---

## Tests Added

`tests/test_survey_operations.py` (9 tests):

| Test | Validates |
|------|-----------|
| `test_empty_village_queue` | No built-up + high confidence → empty queue |
| `test_single_isolated_cluster_ranks_first` | Single cluster → rank 1, isolated access |
| `test_deterministic_ranking` | Same inputs → identical scores and labels |
| `test_score_stability_same_inputs` | Repeated runs → identical top score |
| `test_high_confidence_connected_lower_priority` | Low confidence scores higher than high confidence |
| `test_score_breakdown_present` | Every item has explainable breakdown + reason |
| `test_village_accessibility_score_range` | Score in [0, 100] |
| `test_survey_intelligence_includes_field_verification` | API/report shape + executive summary lead |
| `test_render_overlay_with_queue` | Overlay shape matches RGB input |

Full suite: **44 tests passing**, ~67% coverage.

---

## Example Outputs

### Synthetic village (judge package)

- **Village Accessibility Score:** 27/100
- **Top 3 priorities:**
  1. Verify isolated settlement cluster 3 (no road within 50 m)
  2. Verify isolated settlement cluster 4 (no road within 50 m)
  3. Verify isolated settlement cluster 2 (no road within 50 m)

### Rank #1 queue item (excerpt)

```json
{
  "rank": 1,
  "score": 64.8,
  "centroid_x_px": 499.3,
  "centroid_y_px": 511.6,
  "label": "Settlement Cluster 3",
  "reason": "Settlement Cluster 3: poor road access, large settlement footprint",
  "settlement_area_m2": 9270.0,
  "mean_confidence": 0.5911,
  "access_assessment": "isolated",
  "score_breakdown": {
    "confidence_risk": 40.89,
    "isolation_risk": 100.0,
    "cluster_size": 100.0,
    "water_proximity": 0.0,
    "fragmentation_context": 10.5,
    "weighted_total": 64.84
  }
}
```

### Executive summary (first lines)

```
Village Accessibility Score: 27/100
Priority #1: Verify isolated settlement cluster 3 (no road within 50 m)
Priority #2: Verify isolated settlement cluster 4 (no road within 50 m)
Priority #3: Verify isolated settlement cluster 2 (no road within 50 m)
```

---

## Judge-Facing Value

| What judges see | Why it matters |
|-----------------|----------------|
| **Field Verification Priorities** as first HTML section | Operational story before metrics |
| **“Three places tomorrow”** card + numbered map | 20-second demo moment |
| Ranked table with access + confidence + reason | Actionable, not decorative |
| Per-item score breakdown | No opaque ranking — every score is auditable |
| Village Accessibility Score | Single village-wide readiness index |

---

## Differentiation Assessment

**Would this feature likely increase judge memory and differentiation?**

**Yes — with high confidence on operational value.**

### Evidence

1. **Unique deliverable:** Competitor notebooks typically export masks or IoU tables. This submission outputs a **ranked field visit schedule** with plain-language reasons — directly aligned with SVAMITVA’s survey-officer workflow.

2. **Instant comprehension:** The judge HTML opens with “where to send your field team first,” a numbered map, and three tomorrow-priorities. A non-technical judge can grasp value in under 5 seconds without interpreting segmentation colors.

3. **Explainability as differentiation:** Every rank shows component scores (confidence risk, isolation, size). Judges can challenge or trust the ranking — it is not a black-box “AI said so.”

4. **End-to-end integration:** Same queue appears in `/survey-report` JSON, Streamlit demo, and judge package — one intelligence layer, multiple consumption paths.

5. **Demo script alignment:** Matches the pivot from “model accuracy” to “survey operations briefing” documented in `DEMO_MASTER_SCRIPT.md` and `FAILURE_MODE_STRATEGY.md`.

### Operational value (not model metrics)

- Officers with limited field capacity get **prioritized coordinates** instead of reviewing entire villages.
- Isolation and confidence risks surface **settlements that maps may miss** (0% road access in synthetic demo).
- Accessibility score gives district planners a **single village readiness number** for resource allocation.

This feature does not improve segmentation accuracy; it **converts existing outputs into decisions**. That is the differentiation judges remember when comparing dozens of similar U-Net submissions.

---

## Quick Verification

```bash
# Tests
SVAMITVA_CONFIG_PATH=config/platform_config.synthetic.json .venv/bin/python -m pytest tests/test_survey_operations.py -q

# Judge package
make judge-package   # or scripts/generate_judge_package.py

# Open judge evidence
file:///…/evidence/judge_package/index.html
```
