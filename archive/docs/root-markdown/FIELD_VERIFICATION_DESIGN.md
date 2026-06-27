# Field Verification Priority Queue — Design

## Officer Question

> "I only have one day and one field team. Where should I go first?"

The system answers with a **ranked field verification queue**: ordered visit targets derived deterministically from the segmentation mask and confidence map — no ML, no black box.

---

## Workflow

```
Orthomosaic → Segmentation + Confidence
       ↓
Enumerate candidates:
  (A) Built-up settlement clusters (connected components ≥ 200 px)
  (B) Low-confidence review zones (connected uncertain regions ≥ 500 px)
       ↓
Score each candidate → SurveyPriorityScore (0–100)
       ↓
Deduplicate overlapping candidates (centroid distance < 30 m)
       ↓
Rank descending → field_verification_queue[]
       ↓
Outputs:
  • JSON queue with score breakdown per item
  • Village Accessibility Score (village-wide)
  • Top 3 plain-language priorities for executive summary
  • Numbered overlay map for judge/demo
```

---

## Candidate Types

| Type | Source | Officer meaning |
|------|--------|-----------------|
| `settlement_cluster` | Built-up CC | Verify structures / property boundaries |
| `uncertain_zone` | Confidence < 0.70 CC | Model unsure — human must confirm class |

---

## SurveyPriorityScore (0–100)

Weighted sum of explainable components (each 0–100):

| Component | Weight | Formula |
|-----------|--------|---------|
| **Confidence risk** | 35% | `(1 − mean_confidence) × 100` |
| **Isolation risk** | 30% | `100` if cluster has 0% pixels within 50 m road buffer; else `(100 − local_road_access%)` |
| **Cluster size** | 20% | `min(100, √(area_m²) × 4)` — larger settlements weigh more |
| **Water proximity** | 10% | `% of candidate pixels within 30 m of water × 100` |
| **Fragmentation context** | 5% | `min(100, fragmentation_index × 10)` when village is dispersed |

**Final score:** `clamp(Σ weightᵢ × componentᵢ, 0, 100)`

Every queue item stores `score_breakdown` with each component and weight.

---

## Village Accessibility Score (0–100)

Village-wide index (not per-visit):

```
0.40 × builtup_road_access_pct
+ 0.30 × road_largest_component_pct
+ 0.30 × (1 − min(fragmentation_index / 10, 1)) × 100
```

Uses metrics already computed in `analyze_spatial_intelligence()`.

---

## Access Assessment Labels

| Label | Condition |
|-------|-----------|
| `isolated` | 0% of cluster pixels within 50 m road buffer |
| `partial` | 1–69% within buffer |
| `connected` | ≥ 70% within buffer |
| `n/a` | Uncertain zone not on built-up |

---

## Overlay Design

- Base: RGB ortho (or built-up mask tint if RGB unavailable)
- Numbered circles at queue centroids (1 = highest priority)
- Color: red → orange → yellow by rank
- Legend: "Field visit priority (1 = go first)"

Judge comprehension target: **5 seconds**.

---

## Integration Points

| Consumer | Field |
|----------|-------|
| `build_survey_intelligence()` | `field_verification` dict |
| `executive_summary` | Accessibility score + top 3 priorities first |
| `/survey-report` | via `report.to_dict()` |
| Streamlit | Field priorities expander |
| Judge HTML | Section above all other content |
| `survey_intelligence.json` | Full queue + breakdowns |

---

## Edge Cases

| Case | Behavior |
|------|----------|
| Empty village (no FG) | Empty queue; accessibility from spatial defaults |
| Single cluster | Queue length 1 |
| No confidence map | Use 0.5 mean confidence (neutral risk) |
| No roads | All clusters marked `isolated`; isolation risk = 100 |

---

## Non-Goals

- No route optimization / TSP
- No population estimates
- No LLM-generated reasons — reasons are template-filled from components
