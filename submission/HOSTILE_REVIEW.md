# Hostile Judge Review

Simulated adversarial review from five evaluator personas. Use this to rehearse answers before Q&A.

---

## 1. ISRO Reviewer

**Profile:** Remote sensing scientist. Cares about radiometry, GSD, CRS integrity, and whether metrics are scientifically defensible.

### Hardest Questions

1. "Your validation is only 598 patches from 2 villages — how is this statistically significant for national deployment?"
2. "Did you account for atmospheric correction and orthorectification differences across survey campaigns?"
3. "Patch-based IoU can be inflated by spatial autocorrelation — where is your full-raster evaluation?"
4. "768 px at 0.3 m GSD is 230 m — roads are 1–2 px wide. Your effective resolution is insufficient."
5. "Show me confusion matrices per village, not just IoU."

### Attack Vectors

- Small validation sample size relative to claim scope
- No radiometric normalization across acquisition dates
- Patch sampling may not represent full-raster error distribution
- Thin linear features systematically underestimated at chosen GSD

### Weaknesses They Will Find

- Only 2 validation villages; no cross-state validation
- Per-village variance (NAGUL FG 0.4124) undermines generalization claims
- No sensor-specific calibration documented
- Bridge class failure suggests label/radiometry issues

### Ideal Responses

| Attack | Response |
|--------|----------|
| Small val set | "We report village-held-out patch eval — the correct unit for spatial data. We show per-village stress and do not claim national accuracy. NAGUL proves we report hard cases." |
| Atmospheric correction | "We use survey-grade orthomosaics as delivered by SVAMITVA workflow — same input survey teams use. Our pipeline validates CRS and GSD; radiometric harmonization is a deployment preprocessing step we support via standard GDAL workflows." |
| Patch vs raster | "Certified metrics are patch-based for reproducibility. Full-raster inference is implemented via sliding-window tiling (`src/inference/tiling.py`) and demonstrated in the judge HTML bundle." |
| Road resolution | "Road recall is 0.64 — we find most roads with boundary imprecision. Postprocessing connects fragments. Higher resolution or multi-scale training is our top roadmap item — see IF_WE_HAD_3_MONTHS.md." |

**Evidence to show:** `production_release/metrics/epoch_71_results.json` (per_village_tta), `src/data_validation/validator.py`, `src/inference/tiling.py`

---

## 2. NIC Reviewer

**Profile:** Government IT deployment lead. Cares about security, offline operation, containerization, and integration with existing systems.

### Hardest Questions

1. "Where is your security audit certificate?"
2. "Can this run on air-gapped networks without internet?"
3. "What happens when someone uploads a malicious TIFF?"
4. "How do you manage API keys across 28 states?"
5. "What is your disaster recovery plan for model artifacts?"

### Attack Vectors

- No third-party penetration test on record
- Single-point failure if checkpoint files corrupt
- Upload endpoint attack surface
- No documented SLA or monitoring

### Weaknesses They Will Find

- API key auth is basic (no OAuth/RBAC)
- No centralized model registry integration
- No automated health monitoring dashboard
- Large checkpoint files (748 MB combined) need secure distribution

### Ideal Responses

| Attack | Response |
|--------|----------|
| Security audit | "We implement defense-in-depth: API key auth, upload validation (extension/MIME/size/dimension), weights_only checkpoint loading, CRS allowlists. Formal third-party audit is planned for production rollout — the codebase is structured for it." |
| Air-gapped | "Fully offline. No external API calls. Docker image + recovery_bundle_v1.zip deploy via secure media. Inference is 100% on-premises." |
| Malicious upload | "Upload validator rejects oversized, wrong-format, and extreme-dimension files before they reach inference. See platform_config security block." |
| Key management | "API keys via environment variable SVAMITVA_API_KEY — integrates with existing government secret management (Vault/KMS). Per-state keys rotatable without code changes." |
| Disaster recovery | "SHA-256 checksums on all artifacts in MANIFEST.json. recovery_bundle_v1.zip is the offline backup. Reproducible from git + bundle." |

**Evidence to show:** `config/platform_config.v1.json` (security), `production_release/MANIFEST.json`, `Dockerfile`, `production/api.py`

---

## 3. GIS Expert

**Profile:** State survey department GIS officer. Cares about output format, topology, attribute tables, and QGIS compatibility.

### Hardest Questions

1. "Your road output is fragmented — how is this usable in ArcGIS?"
2. "Do outputs preserve georeferencing and CRS?"
3. "Can I get vector outputs, not just rasters?"
4. "How do you handle topology errors — roads crossing buildings?"
5. "What is the minimum mapping unit for each class?"

### Attack Vectors

- Raster-only output requires vectorization step
- Postprocessing may create topologically invalid geometries
- No documented MMU per class
- Gap-fill may create false connections

### Weaknesses They Will Find

- No built-in raster-to-vector export in demo
- Bridge IoU 0.0 — incomplete feature set for survey maps
- Road gap-fill may connect non-road pixels
- No topology validation (e.g., roads must not overlap water)

### Ideal Responses

| Attack | Response |
|--------|----------|
| Fragmented roads | "Postprocessing gap-fill connects fragments before export. For production GIS, we recommend skeletonization + vectorization with MMU filtering — standard downstream step. We provide the georeferenced mask as input to that workflow." |
| Georeferencing | "Full GeoTIFF output preserves affine transform from source orthomosaic via rasterio. CRS validated on ingest." |
| Vector output | "Masks are GIS-ready GeoTIFFs. Vectorization is a deployment integration step — we can add shapefile export in v1.1. The segmentation quality is the bottleneck we solved." |
| Topology | "Postprocessing order is: predict → gap-fill → bridge recovery. Class priority in rasterization prevents most overlaps. Topology QA is part of human review workflow." |

**Evidence to show:** `src/postprocessing.py`, `src/inference/calibrated_engine.py` (predict_tiff), `src/data_validation/validator.py`

---

## 4. ML Researcher

**Profile:** Academic/competition ML expert. Will challenge architecture choice, baselines, and experimental rigor.

### Hardest Questions

1. "Why not Segment Anything Model (SAM) with prompts?"
2. "Where is your comparison against 5+ baselines?"
3. "Your calibration is just validation set tuning — that's overfitting."
4. "SegFormer is SOTA — why did you use DeepLab?"
5. "Epoch 71 selection on the same data you report — p-hacking?"

### Attack Vectors

- Single architecture family in final submission
- Calibration on same patches as reported metrics
- No k-fold cross-validation
- Alternative architectures tested but not in main paper-style table
- Ensemble adds complexity without ablation study in submission docs

### Weaknesses They Will Find

- SegFormer tested but only in archive
- No SAM/foundation model baseline
- Bias search on val set (5 parameters, 598 patches)
- exp09 raw val FG 0.5077 > certified 0.4809 — why not use exp09?

### Ideal Responses

| Attack | Response |
|--------|----------|
| SAM | "SAM needs prompts and is not trained on SVAMITVA classes. Zero-shot SAM underperforms supervised segmentation on domain-specific orthomosaics with 5-class schema. We prioritized measurable supervised performance." |
| Baselines | "We certified 4 checkpoints (epochs 33, 69, 71, 80) plus SegFormer exp04 — all under identical protocol. FINAL_MODEL_RANKING.md is our baseline table." |
| Calibration overfitting | "5 bias parameters on 598 patches is low-dimensional. We also certified alternative epochs — epoch 71 wins regardless. Calibration is standard production practice, reported transparently." |
| Why DeepLab | "SegFormer FG 0.4038 vs DeepLab 0.4809 — measured, not assumed. We chose the winner." |
| exp09 vs V1 | "exp09 raw val FG 0.5077 was uncorrected, single-checkpoint, marathon-regressed to 0.4493 by ep86. Full calibrated post-eval was not completed (OOM). V1 epoch_71 is certified end-to-end at 0.4809." |

**Evidence to show:** `production_release/reports/FINAL_MODEL_RANKING.md`, `archive/experiment/exp04_segformer_b3/SEGFORMER_FINAL_VERDICT.md`, `submission/JUDGE_OBJECTIONS.md`

---

## 5. Government Deployment Reviewer

**Profile:** Ministry program director. Cares about impact, cost, timeline, and whether this solves a real problem.

### Hardest Questions

1. "What is the measurable impact on property card issuance timeline?"
2. "How many surveyor-hours does this save per village?"
3. "What is the total cost of ownership for 6 lakh villages?"
4. "Why should we trust AI over trained GIS officers?"
5. "What is your plan for continuous model updates as new surveys arrive?"

### Attack Vectors

- No pilot deployment with measured time savings
- No TCO analysis document
- Accuracy on hard villages (NAGUL) may increase review burden
- No formal MLOps pipeline for retraining

### Weaknesses They Will Find

- Impact claims are qualitative, not pilot-validated
- Bridge class non-functional
- Requires GPU for practical throughput
- No state-level rollout plan

### Ideal Responses

| Attack | Response |
|--------|----------|
| Impact on property cards | "SVAMITVA bottleneck is map feature extraction before field verification. We automate roads, settlements, and water — the three classes survey teams spend the most time digitizing. This shifts human effort from tracing to verifying." |
| Surveyor hours | "Manual digitization: days per village. Our inference: minutes on GPU. Even with 50% review time, net savings are an order of magnitude. Pilot measurement is our month-1 roadmap item." |
| TCO | "One GPU server processes thousands of villages/year. Software is open-source Python + Docker. No per-village license. Primary cost is compute hardware and integration — not model API fees." |
| Trust AI | "We do not replace surveyors. We provide draft maps + confidence flags. Human verification is mandatory. The system prioritizes where humans should look." |
| Continuous updates | "Versioned releases (v1.0-certified frozen). New surveys trigger retraining on expanded village set with same certification protocol. production_release/ model is immutable; v1.1 requires beating 0.4809 FG mIoU." |

**Evidence to show:** `src/intelligence/survey_operations.py`, `submission/ONE_PAGE_EXECUTIVE_BRIEF.md`, `submission/IF_WE_HAD_3_MONTHS.md`

---

## Cross-Reviewer Kill Shots (Prepare For These)

| Question | One-Line Defense |
|----------|------------------|
| "Your numbers are too good to be true" | "Reproduce them: `run_calibrated_eval.py --require-bias`. Checksums in MANIFEST.json." |
| "You only have 8 villages" | "That is the competition data. We split 6/2 by village and report per-village variance." |
| "Road IoU is below 0.5" | "Roads are 1–2 px wide with 0.64 recall. We find them; boundaries need refinement." |
| "Why not use GPT/LLM vision?" | "We need georeferenced class masks, not captions. Segmentation is the correct task formulation." |
| "This won't work in my state" | "Correct — NAGUL proves domain shift. Deployment requires local validation. We provide the tools." |

---

## Rehearsal Protocol

1. Each team member takes one persona for 15-min mock Q&A.
2. Answer short form first (20 sec), then technical if pressed.
3. Always point to a file hash or script — never argue from slides alone.
4. If you do not know: "That is not in our certified scope — here is what we measured."
