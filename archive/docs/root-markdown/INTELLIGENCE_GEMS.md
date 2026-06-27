# Intelligence Gems — Extreme Differentiation Search

**Constraint:** No new ML. No architecture swaps. Only capabilities derivable from existing masks, logits, confidence maps, and geospatial metadata.

**Code audit basis:** `spatial_analysis.py`, `explainability.py`, `village_stats.py`, `postprocessing.py`, `survey_report.py`, `calibrated_engine.patch_stats`, demo UI.

---

## Phase 1 — Twenty Latent Capabilities (Not Fully Surfaced)

| # | Capability | Already computable from | Value | Effort | Judge impact |
|---|------------|-------------------------|-------|--------|--------------|
| 1 | **Field verification priority queue** | review zones + isolated built-up clusters + road buffer | Survey teams get ranked visit list | Medium (8h) | **Very high** |
| 2 | **Per-cluster road isolation map** | built-up CC + road dilation | Shows which hamlets lack access | Medium (6h) | **Very high** |
| 3 | **Village accessibility score (0–100)** | road access %, fragmentation, road largest-component % | Single memorable KPI | Low (4h) | High |
| 4 | **Review-zone overlay PNG** | `explainability.review_zones` + mask | Visual field-planning artifact | Low (3h) | High |
| 5 | **Georeferenced visit waypoints** | review centroids + rasterio transform | GIS-importable field routes | Medium (6h) | High |
| 6 | **Flood-proximity hazard mask** | water buffer ∩ built-up | Planning setback enforcement | Low (4h) | Medium |
| 7 | **Road network criticality gaps** | skeleton endpoints after `road_gap_fill` diff | Engineering maintenance priority | Medium (8h) | Medium |
| 8 | **Property inventory estimate** | `VillageReport` rooftop heuristic | SVAMITVA parcel proxy | **Done in code** | Not surfaced in judge pack |
| 9 | **Building density heatmap** | per-patch building count / ha | Development intensity map | Medium (6h) | Medium |
| 10 | **Water access equity index** | distance from each built-up cluster to nearest water | Rural water planning | Medium (8h) | Medium |
| 11 | **Infrastructure balance ratio** | road_length / builtup_area | Urban form diagnostic | Low (2h) | Low |
| 12 | **Confidence-weighted built-up area** | built-up pixels × confidence | Trust-adjusted statistics | Low (3h) | Medium |
| 13 | **Full `VillageReport.summary()` text** | already in `village_stats.py` | Officer-readable printout | **Done** | Not in judge HTML |
| 14 | **Road avg width anomaly flag** | `RoadStats.avg_width_m` | Illegal encroachment hint | Low (2h) | Low |
| 15 | **Settlement cluster cards** | per built-up CC stats + distance to road | Micro-planning per hamlet | Medium (8h) | High |
| 16 | **Survey completion readiness %** | high_confidence_pct weighted by class importance | QA sign-off metric | Low (4h) | Medium |
| 17 | **Disconnected road component map** | road CC labeling | Connectivity investment map | Low (4h) | Medium |
| 18 | **Bridge crossing inventory** | `BridgeStats.bridge_locations` | Non-operational but unique | **Done** | Hidden (bridge non-op) |
| 19 | **Multi-class uncertainty hotspots** | per-class low confidence regions | Targeted re-flight zones | Medium (6h) | Medium |
| 20 | **GeoJSON export of intelligence** | all centroids + polygons | State GIS workflow integration | Medium (8h) | High |

---

## Phase 2 — Second-Order Intelligence Products (30+, Ranked)

Ranked by **government usefulness × demo wow × implementability**.

| Rank | Product | Inference |
|------|---------|-----------|
| 1 | **Field visit priority queue** | uncertain zones ∪ road-isolated clusters, ranked by area × (1 − access) |
| 2 | **Isolated settlement detection** | built-up CC with zero overlap road 50 m buffer |
| 3 | **Village accessibility score** | weighted: road access (40%), road connectivity (30%), fragmentation inverse (30%) |
| 4 | **Flood exposure built-up %** | built-up ∩ water 30 m buffer (exists; not mapped) |
| 5 | **Road network fragmentation index** | components + largest-component % (exists; not branded) |
| 6 | **Settlement fragmentation index** | exists in `spatial_intelligence` |
| 7 | **Probable property count** | rooftop heuristic count (exists in infrastructure) |
| 8 | **Survey automation readiness** | % high-confidence on built-up + road classes |
| 9 | **Critical connectivity gap list** | road skeleton endpoint pairs within gap threshold |
| 10 | **Water body dependency map** | built-up distance to nearest water per cluster |
| 11 | **Development pressure index** | building_density_per_ha (computed, underused) |
| 12 | **Infrastructure deficit index** | road_m per builtup_ha vs village typology threshold |
| 13 | **Review zone severity rank** | review zones sorted by area × (1 − mean_confidence) |
| 14 | **Per-hamlet access card** | cluster ID, buildings, m to nearest road, priority |
| 15 | **Encroachment risk flag** | built-up in water buffer > threshold |
| 16 | **Road coverage adequacy** | road_length / sqrt(total_area) vs norm |
| 17 | **Dispersed settlement flag** | fragmentation > 8 (rule exists) |
| 18 | **Centralized settlement flag** | fragmentation < 3 + access > 80% |
| 19 | **Dual-risk zones** | low confidence AND no road access |
| 20 | **Water-locked settlements** | cluster surrounded by water buffer |
| 21 | **Rooftop vs land-built-up split** | rooftop count vs total buildings |
| 22 | **Largest water body dominance** | largest_body / total_water |
| 23 | **Bridge crossing gap** | road components separated by water without bridge |
| 24 | **Confidence-adjusted road length** | skeleton length × mean road confidence |
| 25 | **Field team workload estimate** | review zones count × avg visit time |
| 26 | **Automated vs manual survey split** | high_conf % by built-up area |
| 27 | **Seasonal flood review trigger** | water proximity > 15% rule (exists) |
| 28 | **Cluster-based mapping workflow trigger** | fragmentation rule (exists) |
| 29 | **Night-light proxy absent** | N/A — reject (no data) |
| 30 | **Population estimate** | N/A — reject (would hallucinate) |

---

## Phase 3 — WOW Test (60-Second Demo Memory)

| Candidate | Remember 1 hr later? | Verdict |
|-----------|----------------------|---------|
| Field visit priority queue (#1) | **Yes** — "they gave a to-do list for surveyors" | **KEEP** |
| Isolated settlement map (#2) | **Yes** — visual, emotional | **KEEP** |
| Village accessibility score (#3) | **Yes** — single number | **KEEP** |
| Flood hazard mask | Maybe | KEEP if paired with #2 |
| Road gap list | No — too engineering | REJECT for demo |
| Infrastructure balance ratio | No | REJECT |
| GeoJSON export | No — invisible in demo | REJECT for wow (keep for GIS judges) |
| Building density heatmap | Maybe | Secondary |
| mIoU table | **No** (negative) | REJECT |

---

## Phase 4 — Government Workflow Replacement

| Manual workflow today | Partial automation | Time saved | Burden reduced |
|----------------------|-------------------|------------|----------------|
| Officer walks ortho marking buildings | Rooftop + building count | 4–8 hrs/village → minutes | High |
| GIS analyst measures road length | Skeleton length × GSD | 2–4 hrs → seconds | High |
| Planner identifies flood-adjacent structures | Water 30 m buffer ∩ built-up | 3–6 hrs → seconds | High |
| Survey chief plans field verification | **Not automated today** — priority queue would replace whiteboard planning | 2–4 hrs → 5 min | **Very high** |
| QA lead finds low-confidence areas | Review zones exist but **no ranked queue** | 1–2 hrs → minutes | High |
| Connectivity assessment for PMGSY-style planning | Fragmentation + gap metrics partial | 4 hrs → 10 min | Medium |
| Written briefing to Panchayat | Executive summary exists | 1 hr → instant | Medium (already done) |

**Biggest unreplaced workflow:** **Field visit planning** — no ranked priority output yet.

---

## Phase 5 — Intelligence Layer V2 (Reasoning, Not ML)

**Module name:** `survey_operations.py` — deterministic reasoning over existing outputs.

### Composite indices (all computable)

```
VillageAccessibilityScore = 
  0.40 × (builtup_road_access_pct / 100) +
  0.30 × (road_largest_component_pct / 100) +
  0.30 × (1 − min(fragmentation_index / 10, 1))

InfrastructureDeficitIndex = 
  max(0, 1 − (road_length_m / (builtup_area_ha × 500)))  # 500 m road/ha norm

SurveyPriorityScore (per zone z) =
  (area_ha_z) × (1 − mean_confidence_z) × (1 if road_isolated else 0.5)
```

### Outputs

| Output | Type |
|--------|------|
| `village_accessibility_score` | float 0–100 |
| `infrastructure_deficit_index` | float 0–1 |
| `field_verification_queue` | ranked list[{rank, centroid_px, reason, score, area_m2}] |
| `isolated_settlements` | list[{cluster_id, n_buildings, distance_to_road_m}] |
| `intervention_recommendations` | extends existing rules with priority tags |

**No new data. No LLM. Pure geometry + confidence.**

---

## Phase 6 — Competitive Moat

| Moat | Why hard to replicate quickly |
|------|------------------------------|
| **SVAMITVA-specific rules** (50 m road access, 30 m water buffer, fragmentation thresholds) | Domain knowledge embedded in `spatial_analysis.py` |
| **Survey officer briefing pipeline** | End-to-end: mask → JSON → API → Streamlit — not a Kaggle notebook |
| **Explainability + spatial fusion** | Competitors have Grad-CAM; you have **visit queues tied to access geometry** |
| **Geospatial correctness chain** | CRS + GSD + GeoTIFF — ML teams often skip |
| **Honest governance** | Bridge non-operational — trust moat in government context |

**Not a moat:** Raw mIoU, model size, transformer architecture.

---

## Phase 7 — Implementation Filter (1–2 Days, Low Risk)

| Capability | Judge impact | Practical value | Risk | Keep? |
|------------|--------------|-----------------|------|-------|
| Field verification priority queue | Very high | Very high | Low | **YES** |
| Isolated settlement detection + overlay | Very high | High | Low | **YES** |
| Village accessibility score | High | High | Low | **YES** |
| Review zone overlay PNG | High | Medium | Low | **YES** |
| `VillageReport.summary()` in judge HTML | Medium | Medium | Very low | **YES** |
| GeoJSON export | Medium | High | Medium | Defer |
| Road criticality gaps | Medium | Medium | Medium | Defer |
| Water equity index | Medium | Medium | Medium | Defer |

---

## Phase 8 — Final Output

### Top 10 Hidden Gems

| Gem | Why it matters | Effort | Demo value | Risk |
|-----|----------------|--------|------------|------|
| 1. Field verification queue | Replaces manual field planning | 8h | **Wow** | Low |
| 2. Isolated settlement map | Visual, unique to GIS+AI | 6h | **Wow** | Low |
| 3. Village accessibility score | One number judges remember | 4h | High | Low |
| 4. Rooftop property inventory | SVAMITVA parcel proxy | 0h (exists) | Medium | Surface only |
| 5. Review zone overlay | Makes explainability visible | 3h | High | Low |
| 6. `VillageReport.summary()` text | Officer printout | 2h | Medium | Very low |
| 7. Dual-risk zones (low conf + no road) | Highest-signal visits | 4h | High | Low |
| 8. Flood-proximity built-up map | Planning enforcement | 4h | Medium | Low |
| 9. Per-hamlet cluster cards | Micro-planning | 8h | High | Medium |
| 10. Georeferenced waypoints | GIS integration | 6h | Medium | Medium |

### Top 5 Must-Implement (Before Freeze)

1. **Field Verification Priority Queue** — ranked JSON + top-3 reasons  
2. **Isolated Settlement Overlay** — PNG in judge package  
3. **Village Accessibility Score** — in executive summary  
4. **Review Zone Overlay** — numbered zones on map  
5. **Wire all into `build_survey_intelligence()` + judge HTML**

**Total effort:** ~1.5 days  
**Expected score impact:** +0.3–0.5 composite (impact + innovation dimensions) without changing mIoU

### Top 3 Judge-Wow Moments

1. **"Here is tomorrow's field visit queue, ranked 1–5"** — read top item aloud  
2. **Map showing isolated hamlets highlighted** — "these settlements have no road access in the model"  
3. **Single score: "Village Accessibility: 34/100"** — instant comprehension

### Top Government Use Cases

| Use case | Stakeholder | Artifact |
|----------|-------------|----------|
| Field verification planning | Survey teams | Priority queue JSON |
| Rural road connectivity gap briefing | Panchayat / PMGSY | Isolation map + fragmentation stats |
| Flood setback compliance screening | Planning officer | Water-proximity % + hazard overlay |
| Automated survey QA sign-off | State GIS | High-confidence % + review zones |
| API integration for district dashboard | State GIS dept | `/survey-report` extended JSON |

### Competitive Moats

- Domain-specific spatial rules (50 m / 30 m buffers) tuned to SVAMITVA  
- Mask → officer briefing pipeline (not mask → CSV)  
- Field queue fusion of **confidence + accessibility** (rare in hackathon submissions)  
- Geospatial production path (CRS, GeoTIFF, API)

### Expected Score Impact

| Dimension | Gain | Mechanism |
|-----------|------|-----------|
| Real-world impact | +0.4–0.6 | Field queue replaces manual planning |
| Innovation | +0.2–0.4 | Reasoning layer beyond segmentation |
| Demo quality | +0.2–0.3 | Visual isolation map + ranked list |
| AI performance | 0 | Unchanged |
| **Composite** | **+0.3–0.5** | Without mIoU improvement |

---

## Single Highest-Leverage Missing Capability

**Field Verification Priority Queue** — a ranked, explainable list merging low-confidence review zones and road-isolated built-up clusters into survey-officer visit priorities, with a numbered overlay map in the judge package.

**Why exactly one:**
- Uses 100% existing outputs (mask, confidence, road buffer geometry already in `spatial_analysis` + `explainability`)  
- No competitor notebook produces a **visit schedule**  
- 60-second demo wow: *"Stop #1: 2.3 ha low-confidence zone, no road within 50 m — send Team A first"*  
- Directly replaces the largest unreplaced manual workflow (Phase 4)  
- Implementable in ~8 hours inside `src/intelligence/survey_operations.py` without touching ML

**Not chosen over this:**
- Accessibility score alone — memorable but not actionable  
- GeoJSON export — high value for GIS, low demo wow  
- VillageReport.summary() — surfacing only, not differentiation

---

*Implementation sketch: `build_field_verification_queue(mask, confidence_map, pixel_size_m) → list[FieldVisitPriority]` wired into `survey_report.py` and `generate_judge_package.py` overlay `07_field_priority_map.png`.*
