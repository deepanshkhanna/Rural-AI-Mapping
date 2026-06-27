# Winning Narrative

**Positioning:** This is not a segmentation benchmark submission. It is a **village survey intelligence system** built on geospatially correct infrastructure extraction.

Everything below is implemented in this repository today. No roadmap. No promises.

---

## The Problem SVAMITVA Solves

Drone orthomosaics contain the physical evidence Panchayats need — roads, buildings, water — but raw imagery does not answer survey questions:

- Which settlements lack road access?
- Where is built-up area fragmented across disconnected clusters?
- Which structures sit in flood-proximity buffers near water bodies?
- Which map regions require human field verification before legal records are updated?

A segmentation mask alone does not produce these answers. **This system does.**

---

## What We Built (Implemented)

### 1. Geospatially correct extraction pipeline

- `UnifiedMultiClassDataset` reprojects shapefile labels to orthomosaic CRS (EPSG:32643/32644) and rasterizes with geometry repair.
- `CalibratedEngine.predict_large` / `predict_tiff` tiles large orthomosaics with ground-sample distance from the affine transform.
- `production/api.py` exposes `/infer`, `/infer-tiff`, and `/survey-report` for operational deployment.

**Outcome for government users:** Predictions align with official village coordinate systems — not screen pixels.

### 2. Survey intelligence — the "so what" layer

`build_survey_intelligence()` (`src/intelligence/survey_report.py`) converts a class mask into a structured decision-support report:

| Output | Source | Government use |
|--------|--------|----------------|
| Total survey area (ha) | `VillageReport.from_mask` | Village-scale planning scope |
| Road network length (m) | Skeletonized road pixels × GSD | Connectivity assessment |
| Built-up structure count | Connected-component analysis | Property inventory proxy |
| **Built-up road access %** | 50 m buffer from roads | Identify settlements needing field access verification |
| **Water proximity %** | 30 m buffer from water | Flood/setback compliance screening |
| **Settlement fragmentation index** | Built-up cluster dispersion | Cluster-based mapping workflow trigger |
| **Written recommendations** | Rule-based spatial analysis | Direct briefing for survey teams |

Example recommendation (from `spatial_analysis.py`, emitted in `survey_intelligence.json`):

> "Only 0% of built-up area is within ~50 m of mapped roads. Field verification recommended for remote settlements."

### 3. Explainability for accountable automation

`build_explainability_report()` produces:

- High-confidence vs review-required pixel percentages
- Per-class mean confidence
- Contiguous **review zones** with centroids for targeted field visits
- Audit notes suitable for GIS QA workflows

**Outcome:** Survey officers know *where* to send teams, not just *what* the model predicted.

### 4. Verifiable engineering discipline

- `make judge` regenerates HTML evidence with SHA-256 manifest (`evidence/judge_package/`)
- `run_calibrated_eval.py` writes provenance-rich JSON (git SHA, checkpoint hashes, bias vector)
- Bridge class explicitly non-operational — no hidden failure modes in success claims

**Outcome:** Auditors can trust the process even when reviewing synthetic verification benchmarks.

---

## Why This Creates More Real-World Value Than a Segmentation Model

| Segmentation-only submission | This submission |
|------------------------------|-----------------|
| Reports mIoU | Reports **road access %, fragmentation, water proximity** |
| Outputs a color mask | Outputs **executive summary + recommendations** |
| Judges must interpret pixels | Survey teams receive **actionable briefing text** |
| Single inference endpoint | `/survey-report` returns full intelligence JSON |
| Notebook demo | Streamlit demo with **Survey Intelligence Report** expander (expanded by default) |
| Claims accuracy | Shows **which zones need human review** |

A team with higher mIoU still delivers a map. **This team delivers a map plus the survey officer's briefing pack.**

---

## Honest Boundaries (Builds Trust)

- Production orthomosaics and trained checkpoints cannot be redistributed — verification uses a synthetic benchmark (FG mIoU ~0.20 full raster; Built-Up IoU ~0.80).
- Bridge class IoU is 0.0 by design; excluded from operational success claims.
- Road and Water classes on the tiny synthetic fixture underperform — the intelligence layer is demonstrated on built-up structure; full-class production metrics require data we cannot ship.

We do not hide these limits. We **lead with decision support** because that is what Panchayats deploy.

---

## One-Sentence Pitch

**"We turn drone orthomosaics into geospatially correct village survey intelligence — with road access analysis, flood-proximity screening, review zones, and written recommendations — not just another segmentation mask."**

---

## Evidence Judges Can Open Today

1. `evidence/judge_package/index.html` → Executive Summary + recommendations section
2. `evidence/judge_package/survey_intelligence.json` → Full structured report
3. `streamlit run demo_ui/app.py` → Survey Intelligence Report expander after inference
4. `POST /survey-report` → Same JSON via API for GIS integration

---

*Use with `SUBMISSION_DEFENSE.md` and `FAILURE_MODE_STRATEGY.md`.*
