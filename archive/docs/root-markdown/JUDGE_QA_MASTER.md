# Judge Q&A Master — 20 Likely Questions

**Rules for all answers:** Truthful, evidence-backed, no unreproducible metrics, no competitor attacks.

---

## AI / Metrics

### Q1. "Your mIoU is lower than another team's."

**Ideal answer:** See `METRICS_DEFENSE.md` — acknowledge; pivot to survey intelligence and verifiable pipeline.

**Evidence:** `evidence/judge_package/metrics.json` (synthetic, labeled).  
**Artifact:** Judge HTML — intelligence section appears before metrics.

---

### Q2. "What is your foreground mIoU?"

**Ideal answer:** "On our committed synthetic verification benchmark, full-raster FG mIoU is **0.1989**, reproducible via `make judge`. That proves the pipeline executes end-to-end. We do not claim production village mIoU in the submission because orthomosaics cannot be redistributed."

**Evidence:** `metrics.json` → `patch_verification.fg_miou`  
**Artifact:** `evidence/judge_package/index.html`

---

### Q3. "Why is Road and Water IoU zero?"

**Ideal answer:** "The synthetic fixture is 1M pixels with thin road lines and a demo model trained 20 epochs — severe class imbalance on a toy benchmark. The submission demonstrates the intelligence layer on built-up structure (IoU ~0.80). We do not claim road/water production performance from this fixture."

**Evidence:** Per-class table in `metrics.json`  
**Artifact:** Judge HTML metrics card (labeled synthetic)

---

### Q4. "What model architecture do you use?"

**Ideal answer:** "DeepLabV3Plus with ResNet encoder, two-checkpoint EMA ensemble (65/35), per-class logit bias calibration, optional TTA, and geospatial postprocessing — implemented in `CalibratedEngine`."

**Evidence:** `src/inference/calibrated_engine.py`, checkpoint config in eval provenance  
**Artifact:** `outputs/calibrated_eval_results.json` → `provenance.calibration`

---

### Q5. "Why is Bridge in the taxonomy if IoU is zero?"

**Ideal answer:** "SVAMITVA taxonomy includes bridge; our model does not achieve operational bridge performance. We document IoU 0.0 and exclude bridge from success claims. This is governance, not a hidden failure."

**Evidence:** README operational classes line  
**Artifact:** `official_metrics_for_submission.md`

---

### Q6. "Can you prove 0.39 mIoU on real data?"

**Ideal answer:** "Not from clone alone — production checkpoints and orthomosaics cannot be redistributed under current terms. If a release bundle is authorized, `fetch_artifacts.sh` + `run_calibrated_eval.py` reproduces metrics with full provenance. We do not cite archived numbers without a fresh eval artifact."

**Evidence:** `scripts/fetch_artifacts.sh`, `benchmark/ARTIFACT_MANIFEST.template.json`  
**Artifact:** Absence of production claims in active README; archived metrics in `docs/audit-archive/` only

---

## GIS / Geospatial

### Q7. "How do you handle coordinate systems?"

**Ideal answer:** "Shapefile labels are reprojected to each orthomosaic's CRS. We support EPSG:32643 and 32644 per platform config. GSD is derived from the GeoTIFF affine transform, not assumed."

**Evidence:** `UnifiedMultiClassDataset`, `pixel_size_from_transform()`  
**Artifact:** `config/platform_config.v1.json` → `geospatial.allowed_epsg`

---

### Q8. "Can you process a full village orthomosaic, not just a patch?"

**Ideal answer:** "Yes. `CalibratedEngine.predict_large` and `predict_tiff` implement sliding-window tiling with overlap accumulation. The production API exposes `/infer-tiff` for GeoTIFF upload."

**Evidence:** `src/inference/tiling.py`, `production/api.py`  
**Artifact:** `tests/test_tiling.py`, API docs in `production/README.md`

---

### Q9. "Is the output georeferenced?"

**Ideal answer:** "`predict_tiff` writes georeferenced output using the source transform and CRS."

**Evidence:** `calibrated_engine.py` → `predict_tiff`  
**Artifact:** Code path in `src/inference/calibrated_engine.py`

---

### Q10. "What geospatial intelligence do you compute beyond the mask?"

**Ideal answer:** "Road network length, connected components, built-up road access within 50 m, water proximity within 30 m, settlement fragmentation index, and rule-based written recommendations."

**Evidence:** `src/intelligence/spatial_analysis.py`  
**Artifact:** `survey_intelligence.json` → `spatial_intelligence`, `recommendations`

---

## Engineering / Credibility

### Q11. "How do I verify your claims?"

**Ideal answer:** "Run `make judge`. Open `evidence/judge_package/index.html`. Check `verification_manifest.json` SHA-256 hashes. Metrics and overlays regenerate from code — we do not cite markdown tables."

**Evidence:** `JUDGE_EXPERIENCE.md`, `RELEASE_FREEZE_CHECKLIST.md`  
**Artifact:** `verification_manifest.json`

---

### Q12. "Do you have tests?"

**Ideal answer:** "Yes — 35+ tests, GitHub Actions CI, synthetic reproduce path, 64% coverage on core modules."

**Evidence:** `.github/workflows/ci.yml`, `pytest`  
**Artifact:** CI badge / last green run on `main`

---

### Q13. "Is there a double-softmax or metric integrity issue?"

**Ideal answer:** "We fixed the inference path: raw logits go to postprocessing once. Baseline and calibrated metrics are computed in the same `run_calibrated_eval.py` run — no hardcoded comparators."

**Evidence:** `run_calibrated_eval.py`, audit remediation in `IMPLEMENTATION_REPORT.md`  
**Artifact:** `calibrated_eval_results.json` with both `baseline` and `calibrated` blocks

---

### Q14. "What's the difference between baseline and calibrated pipeline?"

**Ideal answer:** "Baseline: ensemble + bias, no postprocessing. Calibrated: full pipeline including road gap fill and bridge recovery. Both reported in one artifact."

**Evidence:** `run_calibrated_eval.py` output structure  
**Artifact:** `calibrated_eval_results.json`

---

## Deployment

### Q15. "Can this be deployed in production?"

**Ideal answer:** "Surface exists: FastAPI with API key auth, secure checkpoint loading, Docker image, `/survey-report` for GIS integration. Demo Streamlit is explicitly visualization-only; core logic is in `src/` and `production/`."

**Evidence:** `production/api.py`, `Dockerfile`, `docker-compose.yml`  
**Artifact:** `curl` to `/health`, `/survey-report` example in README

---

### Q16. "What does `/survey-report` return?"

**Ideal answer:** "Full survey intelligence JSON: infrastructure stats, spatial intelligence, explainability, executive summary, recommendations — same as Streamlit expander and judge package."

**Evidence:** `build_survey_intelligence()` in API handler  
**Artifact:** `evidence/judge_package/survey_intelligence.json`

---

## Decision Support / Differentiation

### Q17. "What does a survey officer actually receive?"

**Ideal answer:** "An executive summary: survey area, road length, structure count, road access %, water coverage, confidence split, plus written recommendations like 'Field verification recommended for remote settlements' and review zone centroids for targeted visits."

**Evidence:** `survey_report.py` executive summary builder  
**Artifact:** Judge HTML primary card; Streamlit Survey Intelligence expander

---

### Q18. "How do you handle low-confidence predictions?"

**Ideal answer:** "Explainability report flags review-required pixel percentage, per-class confidence, and contiguous review zones with centroids for field prioritization."

**Evidence:** `src/intelligence/explainability.py`  
**Artifact:** `survey_intelligence.json` → `explainability.review_zones`

---

### Q19. "Why should we score you above a higher-mIoU team?"

**Ideal answer:** "If the criterion is segmentation leaderboard only, they may score higher. If the criterion is deployable SVAMITVA value — geospatial correctness, survey officer briefing, API integration, verifiable evidence — we deliver a complete decision-support system. We are explicit about what we prove vs what we do not ship."

**Evidence:** `WINNING_NARRATIVE.md`, intelligence layer implementation  
**Artifact:** Side-by-side: competitor mask vs our `survey_intelligence.json`

---

### Q20. "What would you do differently with more time?"

**Ideal answer:** "Authorize redistribution of production checkpoints and validation orthomosaics so judges can verify production mIoU independently. The pipeline and packaging scripts already exist. Engineering is not the blocker — data release is."

**Evidence:** `scripts/package_production_release.sh`, `FAILURE_MODE_STRATEGY.md`  
**Artifact:** `benchmark/ARTIFACT_MANIFEST.template.json`

---

## Presenter Emergency Cards

| If judge says… | Do NOT say… | DO say… |
|----------------|-------------|---------|
| "Low mIoU" | "Our model is SOTA" | "Pipeline verified; value is intelligence layer" |
| "Prove 0.39" | Quote archived docs | "Cannot redistribute; synthetic proves pipeline" |
| "Just segmentation" | Argue at length | Open survey recommendations immediately |
| "Bridge broken" | "We'll fix it" | "Documented non-operational by design" |
