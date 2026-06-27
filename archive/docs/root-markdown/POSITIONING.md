# Positioning — Geospatial Decision-Support System

**Reframe:** Not "another segmentation project."  
**Position:** A **geospatial decision-support system** that converts drone orthomosaics into village survey intelligence for Panchayati Raj / SVAMITVA workflows.

All statements below map to implemented code. No roadmap.

---

## One-Sentence Description

**We convert drone orthomosaics into geospatially correct village survey intelligence — road access analysis, settlement fragmentation, explainability review zones, and written field recommendations — not just a segmentation mask.**

---

## 30-Second Description

SVAMITVA villages need more than colored pixels on a map. Survey officers need to know which settlements lack road access, where built-up areas are fragmented, which zones require human verification, and what to tell field teams.

We built an end-to-end system: geospatially correct segmentation on orthomosaics — CRS handling, tiling, GeoTIFF I/O — plus a **survey intelligence layer** that produces executive summaries and written recommendations. Judges can open our evidence pack and see the briefing a survey officer would receive, verifiable with `make judge` and a SHA-256 manifest.

We are honest about scope: bridge class is non-operational; verification metrics are on a synthetic benchmark because production orthomosaics cannot be redistributed.

---

## 2-Minute Description

**Problem:** Panchayats and survey teams receive drone orthomosaics containing roads, buildings, and water — but imagery alone does not answer operational questions. Which structures lack road access? Where is settlement fragmented? What must be field-verified before records are updated?

**Why segmentation alone fails:** A mask is an intermediate product. It does not produce road-access percentages, flood-proximity buffers, review-zone centroids, or written recommendations for field officers.

**What we built:**

1. **Geospatial extraction pipeline** — shapefile labels reprojected to orthomosaic CRS; sliding-window inference on large GeoTIFFs; ground sample distance from affine transforms; FastAPI with `/infer`, `/infer-tiff`, and `/survey-report`.

2. **Survey intelligence layer** — `build_survey_intelligence()` combines infrastructure statistics, spatial connectivity analysis, and explainability into one JSON report: built-up road access %, water proximity %, settlement fragmentation index, confidence-based review zones, and plain-language recommendations.

3. **Verification discipline** — `make judge` regenerates an HTML evidence bundle with cryptographic manifest; metrics are labeled synthetic pipeline verification, not inflated production claims.

**Government value:** A GIS department can integrate via API; a survey team receives a briefing pack, not just a PNG. **Differentiation:** Competitors may report higher mIoU; we deliver the officer's decision-support output.

---

## Technical Description

| Layer | Implementation | Judge-visible artifact |
|-------|----------------|------------------------|
| Data / CRS | `UnifiedMultiClassDataset` — reprojection, geometry repair, rasterization | `docs/ARCHITECTURE.md`, tests |
| Inference | `CalibratedEngine` — EMA ensemble, bias calibration, TTA, tiling | `evidence/judge_package/overlays/` |
| Postprocess | Road gap fill, bridge recovery (non-operational class), rooftop classification | `run_calibrated_eval.py` baseline vs calibrated |
| Intelligence | `spatial_analysis.py`, `explainability.py`, `survey_report.py` | `survey_intelligence.json`, judge HTML executive summary |
| API | FastAPI `/survey-report`, `/infer-tiff`, secure checkpoints | `production/api.py`, Docker |
| Verification | `make judge`, SHA-256 manifest, provenance JSON | `verification_manifest.json`, `calibrated_eval_results.json` |

**Operational classes:** Road, Built-Up Area, Water Body.  
**Non-operational:** Bridge (IoU 0.0, documented).  
**Verification benchmark:** Synthetic 1024×1024 ortho — FG mIoU ~0.20; Built-Up IoU ~0.80 on full raster.

---

## Perception Shift (Before → After)

| Risk perception | Target perception |
|-----------------|-------------------|
| "Segmentation hackathon entry" | "Survey intelligence platform" |
| "Low mIoU" | "Pipeline verified; value is decision support" |
| "Another DeepLab notebook" | "Deployable API + GIS-correct pipeline + officer briefing" |
| "Unverifiable metrics" | "Cryptographic evidence chain; honest synthetic labeling" |

---

*Use with `DEMO_MASTER_SCRIPT.md`, `JUDGE_QA_MASTER.md`, `METRICS_DEFENSE.md`.*
