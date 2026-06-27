# Judge Q&A Master

**Model:** epoch_71 ensemble | **FG mIoU:** 0.4809 | **Release:** v1.0-certified  
**Last updated:** 2026-06-27 | **Ops reference:** `PROJECT_BIBLE.md`

Each entry: **Short** (20–30 sec) → **Technical** (1–2 min) → **Evidence** → **References**

---

## Architecture (Q1–Q5)

### Q1. What model architecture did you use?

**Short:** DeepLabV3Plus with a ResNet50 encoder — a proven semantic segmentation architecture tuned for geospatial orthomosaics at 768-pixel resolution.

**Technical:** We use DeepLabV3Plus from the segmentation-models-pytorch library with a ResNet50 ImageNet backbone. The ASPP module captures multi-scale context critical for roads and water bodies at 0.3 m GSD. The model has 26.7M parameters, outputs 5 classes, and runs through a calibrated two-checkpoint ensemble at inference. We evaluated SegFormer-B3 as an alternative; it underperformed V1 by 7.7 FG mIoU points and was rejected.

**Evidence:** Certified architecture in `config/platform_config.v1.json`; SegFormer rejection FG 0.4038 vs 0.4809.

**References:** `src/models/model_factory.py`, `submission/SUBMISSION_LOCK.md`, `archive/experiment/exp04_segformer_b3/SEGFORMER_FINAL_VERDICT.md`

---

### Q2. Why DeepLabV3Plus and not a newer architecture?

**Short:** Because we measured it. DeepLabV3Plus-ResNet50 beat SegFormer-B3 on our held-out villages after full calibrated evaluation — we chose evidence over novelty.

**Technical:** SegFormer-B3 was trained for 20 epochs with identical data, loss, and eval protocol. Calibrated FG mIoU was 0.4038 vs V1's 0.4809; Road IoU dropped 9.7 points. Transformer attention helps on large datasets; with 6 training villages and severe class imbalance, the CNN inductive bias and ImageNet pretraining were more data-efficient. Architecture swaps without domain-scale data are a common failure mode in remote sensing.

**Evidence:** exp04 calibrated eval table; guardian stopped SegFormer at epoch 10 on gate failure.

**References:** `archive/experiment/exp04_segformer_b3/SEGFORMER_FINAL_VERDICT.md`, `production_release/reports/FINAL_MODEL_RANKING.md`

---

### Q3. What is your inference pipeline beyond the neural network?

**Short:** Ensemble of two checkpoints, per-class logit calibration, test-time augmentation, then geospatial postprocessing — road gap fill and bridge recovery.

**Technical:** At inference we blend epoch-71 weights (65%) with epoch-80 EMA (35%), add tuned per-class biases `[-0.5, 0.75, 0.0, -0.5, -0.5]`, average logits across horizontal and vertical flips, then apply postprocessing: road gap fill connects fragmented road predictions; bridge recovery uses built-up spatial context. Full GeoTIFFs use sliding-window tiling with logit accumulation. This pipeline is what produced 0.4809 FG mIoU — not raw model output alone.

**Evidence:** Baseline without postprocess: FG 0.4810; calibrated with postprocess: 0.4809 (road precision-recall tradeoff documented in epoch_71_results.json).

**References:** `src/inference/calibrated_engine.py`, `src/postprocessing.py`, `production_release/metrics/epoch_71_results.json`

---

### Q4. How many parameters and what is the compute requirement?

**Short:** 26.7 million parameters. Runs on a single GPU; CPU fallback supported for API deployment.

**Technical:** DeepLabV3Plus-ResNet50 is ~27M params. Training used batch 4 with gradient accumulation 8 (effective batch 32) at 768×768. SegFormer-B3 peaked at ~6.3 GB VRAM with batch 2. Production inference tiles large orthomosaics sequentially; a village-scale GeoTIFF processes in minutes on a mid-range GPU. Dockerized FastAPI service is included.

**Evidence:** Parameter count in certification docs; SegFormer GPU memory in exp04 report.

**References:** `submission/SUBMISSION_AUDIT.md`, `production/api.py`, `Dockerfile`

---

### Q5. Why an ensemble of two checkpoints?

**Short:** Epoch 71 has the best aggregate FG mIoU; epoch 80 EMA adds stability. Blending 65/35 improved robustness over either checkpoint alone.

**Technical:** We certified four single-epoch candidates (33, 69, 71, 80) under identical eval protocol. Epoch 71 wins on FG mIoU (0.4809) and Water IoU (0.7466). Epoch 69 has best Road IoU (0.4397) but lower aggregate FG. Epoch 80 alone scores 0.4627. The ensemble captures peak validation performance (epoch 71) while EMA weights from epoch 80 smooth overfitting artifacts. Weights and bias were tuned on validation patches only.

**Evidence:** FINAL_MODEL_RANKING table; ensemble weights in optimal_bias.json.

**References:** `production_release/reports/FINAL_MODEL_RANKING.md`, `production_release/bias/optimal_bias.json`

---

## Training (Q6–Q10)

### Q6. What loss function did you use?

**Short:** A composite Focal Tversky loss designed for severe class imbalance — roads and bridges are tiny fractions of pixels.

**Technical:** Standard cross-entropy under-penalizes rare classes. Our multiclass loss combines Focal Tversky with class-weighted terms emphasizing Road and Bridge recall without collapsing Built-Up precision. Loss version is locked in the training config. We tested road-precision recovery (exp06) and density sampling (exp07) but neither beat V1 on certified eval.

**Evidence:** Loss implementation with class weights; exp06 paused, exp07 gate failed.

**References:** `src/losses/multiclass_loss.py`, `archive/experiment/exp07_road_density_sampler/E07_PROMOTION_DECISION.md`

---

### Q7. How long did you train and on what hardware?

**Short:** 80 epochs on 6 training villages, 150 random patches per image per epoch. Standard single-GPU training.

**Technical:** Training config: 80 epochs, 768 px patches, batch 4 × accumulation 8. Best checkpoint selected at epoch 71; EMA tracked through epoch 80. Post-V1 marathon training to epoch 86 on expanded data showed FG regression (0.5077 raw at ep67 → 0.4493 at ep86), confirming early stopping was correct. We do not claim specific wall-clock hours as a competitive metric — reproducibility is config-locked.

**Evidence:** platform_config.v1.json training block; exp09 marathon report.

**References:** `config/platform_config.v1.json`, `archive/experiment/exp09_8_village_expansion/EXP09_MARATHON_FINAL_REPORT.md`

---

### Q8. How did you select epoch 71 over epoch 80?

**Short:** Same evaluation protocol on 598 held-out patches. Epoch 71 scored highest FG mIoU; epoch 80 alone was worst among candidates.

**Technical:** We ran certification evals for epochs 33, 69, 71, and 80 with identical pipeline: ensemble config per candidate, bias search, TTA, postprocess. Ranking criteria: FG mIoU first, then Road, Water, calibration stability, class balance. Epoch 71: FG 0.4809. Epoch 80 alone: FG 0.4627. Epoch 71 is the `best_model.pth` anchor; epoch 80 contributes via EMA in `latest_model.pth`.

**Evidence:** FINAL_MODEL_RANKING certification table.

**References:** `production_release/reports/FINAL_MODEL_RANKING.md`, `production_release/metrics/epoch_71_results.json`

---

### Q9. Did you use data augmentation?

**Short:** Yes — standard geospatial augmentations during training; separate TTA at inference for flip averaging.

**Technical:** Training transforms include flips, rotations, and color jitter appropriate for orthomosaics (see unified dataset). Inference TTA averages logits from original, horizontal flip, and vertical flip before argmax. TTA improves FG mIoU from 0.4755 to 0.4809 on the certified eval (no-TTA vs TTA in epoch_71_results.json).

**Evidence:** TTA delta in epoch_71_results.json eval_no_tta vs eval_calibrated_tta.

**References:** `src/datasets/unified_dataset.py`, `production_release/metrics/epoch_71_results.json`

---

### Q10. How do you prevent overfitting with only 6 training villages?

**Short:** Held-out village validation, EMA, early checkpoint selection, and rejection of models that regress on validation — not training loss alone.

**Technical:** Train/val split is by entire villages (6 train, 2 val) — no patch leakage across villages. We track per-epoch validation FG mIoU and certified multiple checkpoints. Exp09 added 2 villages and ran 86 epochs; raw val FG peaked at epoch 67 then regressed to 0.4493 by epoch 86 — we rejected that run. Epoch 71 was selected by held-out performance, not training loss. Domain shift between villages (NADALA FG 0.5882 vs NAGUL 0.4124) is reported transparently.

**Evidence:** Per-village stress in epoch_71_results.json; exp09 marathon regression.

**References:** `production_release/metrics/epoch_71_results.json`, `submission/SUBMISSION_AUDIT.md`

---

## Dataset (Q11–Q15)

### Q11. How much data did you train on?

**Short:** Six village orthomosaics for training, two held out for validation — roughly 900 training patches per epoch at 150 patches × 6 images.

**Technical:** Each training village is a GeoTIFF orthomosaic with shapefile labels for Road, Bridge, Built-Up, and Water Body. We sample 150 random 768×768 patches per village per epoch. Validation uses 598 patches across NADALA and NAGUL. Labels are rasterized from official survey shapefiles with CRS validation (EPSG 32643/32644/3857). Raw geodata is not in version control; village list is locked in platform_config.v1.json.

**Evidence:** 598 val patches; 6+2 village split in config.

**References:** `config/platform_config.v1.json`, `src/datasets/unified_dataset.py`, `src/data_validation/validator.py`

---

### Q12. How do you handle coordinate reference systems?

**Short:** We validate CRS on ingest and repair common mismatches before rasterizing labels — geospatial correctness is a first-class requirement.

**Technical:** Allowed EPSG codes: 32643, 32644, 3857. DatasetValidator checks TIFF/shapefile alignment, pixel size (~0.3 m GSD), and extent overlap before training or eval. UnifiedMultiClassDataset performs CRS repair when shapefiles and rasters disagree. This prevents silent label misalignment — a common source of inflated metrics in GIS ML projects.

**Evidence:** CRS allowlist in platform config; validator in CI path.

**References:** `config/platform_config.v1.json`, `src/data_validation/validator.py`, `src/datasets/unified_dataset.py`

---

### Q13. Why only 8 villages total?

**Short:** That is the competition dataset scope we received. We designed for village-level generalization and report per-village variance honestly.

**Technical:** SVAMITVA orthomosaics are expensive to acquire and label. Our split is 6 train / 2 val by village — the correct unit for spatial generalization. NAGUL (FG 0.4124) is harder than NADALA (0.5882), revealing domain shift. We tested adding 2 more training villages (exp09); marathon training regressed on validation. More data helps, but our submission reports metrics on the held-out villages we were given — not extrapolated claims.

**Evidence:** Per-village metrics; exp09 with 8 train villages still rejected.

**References:** `production_release/metrics/epoch_71_results.json`, `submission/SUBMISSION_AUDIT.md`

---

### Q14. How are shapefile labels converted to training masks?

**Short:** Vector polygons are rasterized to the orthomosaic grid with class priority rules — roads and water overwrite background, built-up fills settlement areas.

**Technical:** UnifiedMultiClassDataset loads GeoTIFF + shapefile pairs per village. Polygons are burned into multi-class masks matching raster dimensions. Class IDs: 0 Background, 1 Road, 2 Bridge, 3 Built-Up, 4 Water. Bridge has very few pixels (~6,290 in val) explaining near-zero IoU. Patch sampling uses stratified logic to ensure rare classes appear in training batches.

**Evidence:** Bridge gt_pixels: 6290 in epoch_71_results.json; CLASS_NAMES in unified_dataset.

**References:** `src/datasets/unified_dataset.py`, `production_release/metrics/epoch_71_results.json`

---

### Q15. Did you verify data quality?

**Short:** Yes — automated preflight validation runs before every training and evaluation job.

**Technical:** DatasetValidator checks file existence, CRS, dimensions, label coverage, and class presence. `run_calibrated_eval.py` calls validation by default (`--skip-validation` only for CI synthetic fixtures). Failed validation aborts with actionable error messages. This is part of our reproducibility story — bad data cannot silently produce metrics.

**Evidence:** Validator integrated in run_calibrated_eval.py; synthetic CI fixtures for judge verification.

**References:** `src/data_validation/validator.py`, `run_calibrated_eval.py`, `scripts/reproduce.sh`

---

## Calibration (Q16–Q19)

### Q16. What is logit bias calibration?

**Short:** We add per-class constants to model logits before softmax — tuning precision/recall balance without retraining.

**Technical:** Raw models over-predict dominant classes. We grid-search bias values on validation patches to maximize FG mIoU. Optimal vector: `[-0.5, 0.75, 0.0, -0.5, -0.5]` for [Background, Road, Bridge, Built-Up, Water]. Bias-only FG mIoU reaches 0.5091; combined with TTA and postprocess the certified score is 0.4809. Calibration is cheap, reproducible, and stored as JSON alongside checkpoints.

**Evidence:** bias search FG 0.5091 vs certified 0.4809 in epoch_71_results.json.

**References:** `bias_search.py`, `production_release/bias/optimal_bias.json`, `src/inference/calibrated_engine.py`

---

### Q17. Is calibration just overfitting to validation?

**Short:** It is validation tuning — the same as threshold selection in any production ML system. We report it transparently and lock the values.

**Technical:** Bias search uses the same 598 val patches as final eval. This is intentional: calibration is part of the inference pipeline, not a hidden test-set fit. We mitigate overfitting by (1) low-dimensional search (5 biases), (2) certifying multiple epoch candidates under identical protocol, (3) reporting per-village stress, and (4) freezing bias in production_release with SHA-256 checksum. Alternative epochs (33, 69, 80) were also bias-searched — epoch 71 still wins.

**Evidence:** Four candidates certified with independent bias search; epoch 71 ranks first.

**References:** `production_release/reports/FINAL_MODEL_RANKING.md`, `production_release/bias/optimal_bias.json`

---

### Q18. Why positive bias on Bridge (+0.75) if Bridge IoU is zero?

**Short:** Bridge has almost no pixels in validation. Bias tuning cannot create signal that the model never learned — we do not claim Bridge performance.

**Technical:** Bridge has 6,290 GT pixels vs 6.2M for Road. The +0.75 bias was searched but Bridge IoU remains 0.0 after full pipeline. We include Bridge as a class for SVAMITVA completeness but explicitly exclude it from operational claims. Built-Up and Water biases are negative (-0.5) to reduce false positives on dominant classes.

**Evidence:** Bridge IoU 0.0 with 6290 gt_pixels; documented as unsupported claim.

**References:** `docs/SUBMISSION_GUIDE.md`, `production_release/metrics/epoch_71_results.json`

---

### Q19. Can reviewers reproduce your calibration?

**Short:** Yes — copy optimal_bias.json and run bias_search.py or use the frozen file directly.

**Technical:** `production_release/bias/optimal_bias.json` is checksummed in MANIFEST.json. Reviewers can run `bias_search.py` to re-derive biases (deterministic grid on val patches) or use the frozen file with `run_calibrated_eval.py --require-bias`. CalibratedEngine loads bias from file and reports provenance in eval output JSON.

**Evidence:** SHA-256 `4ff3321b…` for optimal_bias.json; provenance in calibrated_eval_results.json.

**References:** `production_release/MANIFEST.json`, `bias_search.py`, `run_calibrated_eval.py`

---

## Evaluation (Q20–Q24)

### Q20. What is FG mIoU and why do you use it?

**Short:** Mean IoU across Road, Built-Up, and Water — the three operational infrastructure classes for SVAMITVA.

**Technical:** FG mIoU = mean(IoU_Road, IoU_BuiltUp, IoU_Water). Background and Bridge are excluded from the aggregate because Background dominates pixel counts and Bridge lacks usable training signal. This matches the competition's infrastructure focus. We report per-class IoU alongside FG mIoU for full transparency.

**Evidence:** FG mIoU 0.4809; per-class breakdown in epoch_71_results.json.

**References:** `src/evaluation/unified_evaluator.py`, `production_release/metrics/epoch_71_results.json`

---

### Q21. How many validation patches and why patches not full rasters?

**Short:** 598 patches from 2 held-out villages — patch eval is standard for segmentation and matches our training sampling strategy.

**Technical:** Full-raster eval is computationally expensive and sensitive to tiling boundaries. Patch eval on a fixed seed/stratified sample gives reproducible metrics comparable across experiments. 598 patches span both validation villages with class representation. We also support full GeoTIFF inference via sliding-window tiling for deployment and demo. Patch metrics are our certified submission numbers.

**Evidence:** val_patches: 598 in epoch_71_results.json; tiling in calibrated_engine.

**References:** `run_calibrated_eval.py`, `src/inference/tiling.py`, `production_release/metrics/epoch_71_results.json`

---

### Q22. What is your evaluation protocol exactly?

**Short:** Epoch-71 ensemble, frozen bias, TTA on, postprocessing on, 598 val patches, NADALA + NAGUL.

**Technical:** Protocol locked in SUBMISSION_LOCK.md: load best_model.pth (ep71) + latest_model.pth (ep80 EMA), weights 0.65/0.35, bias from optimal_bias.json, TTA enabled, postprocess enabled (road gap fill + bridge recovery). Evaluator: unified_evaluator.compute_counts_metrics. Same protocol used for all candidate ranking. Entry point: `run_calibrated_eval.py --require-bias`.

**Evidence:** Repro command reproduces 0.4809 FG mIoU on real data.

**References:** `submission/SUBMISSION_LOCK.md`, `run_calibrated_eval.py`, `production_release/metrics/epoch_71_results.json`

---

### Q23. How do results vary across villages?

**Short:** NADALA is stronger (FG 0.5882); NAGUL is harder (FG 0.4124). We report both — no cherry-picking.

**Technical:** Per-village TTA metrics in epoch_71_results.json show significant domain shift. NAGUL has narrower roads, different settlement patterns, and fewer training-similar examples. This is expected with 6 training villages and motivates our honest generalization framing. Aggregate FG mIoU 0.4809 is the mean across all 598 patches from both villages.

**Evidence:** per_village_tta section in epoch_71_results.json.

**References:** `production_release/metrics/epoch_71_results.json`, `production_release/reports/WINNER_STRESS_REPORT.md`

---

### Q24. Can judges verify metrics independently?

**Short:** Yes — one command with synthetic fixtures; full production eval with checkpoints and geodata.

**Technical:** `make judge` trains a synthetic verification model and generates HTML evidence with SHA-256 manifest. `make reproduce` runs calibrated eval on synthetic fixtures. For production: copy checkpoints from production_release, run `run_calibrated_eval.py --require-bias` with platform_config.v1.json. Checksums verified via SHA256SUMS.txt. All metrics traceable to code, not markdown.

**Evidence:** 13/13 checksum files verified; reproduce.sh completes in CI.

**References:** `docs/REPRODUCE_RESULTS.md`, `Makefile`, `production_release/checksums/SHA256SUMS.txt`

---

## Deployment (Q25–Q29)

### Q25. Is this production-ready or just a notebook?

**Short:** Production-ready — FastAPI service, Docker, Streamlit demo with GeoTIFF tiling and GeoPackage export, secure checkpoint loading, and API key authentication.

**Technical:** `production/api.py` exposes `/infer` with upload validation (extension, MIME, size, dimension limits). Checkpoints load with weights_only=True. Docker Compose packages the API. Streamlit demo (`demo_ui/app.py`) runs full-resolution GeoTIFF inference via `CalibratedEngine.predict_tiff()`, exports GIS vectors (building footprints, roads, water bodies), and runs experimental roof classification. Config is environment-driven via SVAMITVA_CONFIG_PATH. Note: some environments have a FastAPI/Starlette version conflict in tests — Streamlit demo is the primary judge surface.

**Evidence:** Dockerfile, docker-compose.yml, `src/export/vector_export.py`, `demo_ui/app.py`.

**References:** `production/api.py`, `demo_ui/app.py`, `src/security/checkpoints.py`, `PROJECT_BIBLE.md`

---

### Q26. How do you handle large village orthomosaics at inference?

**Short:** Sliding-window tiling with logit accumulation — processes any GeoTIFF size without loading the full raster into GPU memory.

**Technical:** `src/inference/tiling.py` iterates 768×768 windows with overlap, accumulates logits, and normalizes by coverage count. CalibratedEngine.predict_tiff() handles full-raster export. This is how SVAMITVA-scale orthomosaics (gigapixel) are processed in production without OOM.

**Evidence:** Tiling module with accumulate_logits/finalize_logits.

**References:** `src/inference/tiling.py`, `src/inference/calibrated_engine.py`

---

### Q27. What security controls are implemented?

**Short:** API key auth, upload validation, safe checkpoint loading, and CRS allowlists.

**Technical:** Security config in platform_config.v1.json: max upload 64 MB, max 8192 px dimension, allowed MIME types, API key via x-api-key header. Checkpoint loading rejects unsafe deserialization. No arbitrary code execution paths in inference. Suitable for government deployment with standard reverse-proxy and key management.

**Evidence:** security block in platform_config.v1.json; checkpoints.py weights_only enforcement.

**References:** `config/platform_config.v1.json`, `src/security/checkpoints.py`, `production/api.py`

---

### Q28. What is the demo judges should see?

**Short:** Run Streamlit on an official demo GeoTIFF — live segmentation, experimental roof codes, and GeoPackage download. Offline fallback: `evidence/judge_package/index.html`.

**Technical:** Primary live path: `bash scripts/start_demo_gpu.sh` → http://localhost:8501. Select tile `04_fattu_bhila_building_heavy`, **TTA OFF** (~28s GPU segmentation + ~22s vector/roof export). Show three-panel mask output, then **Experimental Roof Classification** card (~520 footprints, ~36% with `roof_type_code`, distribution table for codes 1–4). Download GPKG → QGIS → `building_footprints.roof_type_code`. Offline: `make judge` generates HTML with GT vs prediction and SHA-256 manifest. `python scripts/build_judge_package.py` builds offline GPKG fallback when GPU unavailable.

**Evidence:** `demo_ui/app.py` roof panel + GPKG export; `demo_dataset/demo_manifest.json` (6 official tiles).

**References:** `PROJECT_BIBLE.md`, `submission/DEMO_PRESENTATION_READY.md`, `demo_ui/app.py`, `scripts/start_demo_gpu.sh`

---

### Q29. How would NIC deploy this?

**Short:** Containerized API behind existing government gateway — no custom infrastructure required.

**Technical:** Standard deployment: Docker image → Kubernetes/VM → API gateway with API key → connect to orthomosaic storage (S3/NAS). Model artifacts from production_release/recovery_bundle_v1.zip. Config via environment variables. Batch inference can run offline on orthomosaic archives; API mode for on-demand village analysis. No dependency on external SaaS or proprietary runtimes.

**Evidence:** Dockerfile, docker-compose.yml, recovery bundle packaging.

**References:** `Dockerfile`, `production_release/recovery_bundle_v1.zip`, `docs/ARCHITECTURE.md`

---

## Scalability (Q30–Q33)

### Q30. Can this scale to all Indian villages?

**Short:** The inference pipeline scales horizontally — training generalization is the bottleneck, not deployment architecture.

**Technical:** Inference is embarrassingly parallel: each orthomosaic is independent, tileable, and stateless. A GPU fleet can process thousands of villages. Generalization to unseen villages requires more diverse training data — we report NAGUL as a hard case (FG 0.4124). Scaling deployment is an engineering problem; scaling accuracy is a data problem. We are honest about which we have solved.

**Evidence:** Tiling inference; per-village variance documented.

**References:** `src/inference/tiling.py`, `production_release/metrics/epoch_71_results.json`

---

### Q31. What is inference latency per village?

**Short:** Minutes per village orthomosaic on a single GPU — depends on TIFF size, not model complexity alone.

**Technical:** Latency is dominated by raster size and tiling count, not forward-pass time per tile. Demo tile `04_fattu_bhila_building_heavy` (8200×8200): ~28s segmentation + ~22s GPKG/roof export on RTX 5070 with TTA off. A 768×768 tile forward pass is sub-second on GPU. Full-village processing pipelines hundreds of tiles sequentially. Large orthos skip slow bridge-recovery postprocess when `h*w > 25M` pixels. For national scale, batch across GPUs.

**Evidence:** Demo timings on `04_fattu_bhila_building_heavy`; eval time 527s for 598 patches in certification.

**References:** `demo_ui/inference_wrapper.py`, `src/inference/calibrated_engine.py`, `PROJECT_BIBLE.md`

---

### Q32. Could you run this on CPU-only government servers?

**Short:** Yes — CPU fallback is supported, with proportionally longer inference time.

**Technical:** CalibratedEngine and API detect device automatically (cuda if available, else cpu). Training on CPU is impractical; inference is feasible for single-village batch jobs. For NIC deployment we recommend GPU nodes for batch processing and CPU for API fallback/low-volume requests.

**Evidence:** DEVICE selection in run_calibrated_eval.py; torch CPU map_location in checkpoint loading.

**References:** `run_calibrated_eval.py`, `src/inference/calibrated_engine.py`

---

### Q33. How do you handle new villages without retraining?

**Short:** Run inference directly — but expect accuracy drop on out-of-distribution villages. We quantify this with NAGUL.

**Technical:** The model is a frozen checkpoint — new villages need only orthomosaic input. No fine-tuning required for deployment. Accuracy on unseen villages depends on visual similarity to training distribution. NAGUL (FG 0.4124) demonstrates the risk. Production deployment should include confidence monitoring and optional human review for low-confidence regions (explainability module in src/intelligence/).

**Evidence:** NAGUL per-village FG 0.4124; explainability module exists.

**References:** `src/intelligence/explainability.py`, `production_release/metrics/epoch_71_results.json`

---

## Government Adoption (Q34–Q37)

### Q34. How does this fit Ministry of Panchayati Raj workflows?

**Short:** It automates the slowest step in SVAMITVA — extracting roads, settlements, and water from orthomosaics that teams currently digitize manually.

**Technical:** SVAMITVA creates property cards from drone surveys. Our system segments infrastructure classes from orthomosaics, producing GIS-ready masks and survey intelligence reports (connectivity, fragmentation, recommendations). This accelerates map preparation before field verification. We output standard GeoTIFF masks compatible with QGIS/ArcGIS workflows used by state survey departments.

**Evidence:** Survey operations and report modules in src/intelligence/.

**References:** `src/intelligence/survey_operations.py`, `src/intelligence/survey_report.py`, `docs/PROJECT_OVERVIEW.md`

---

### Q35. What is the cost compared to manual digitization?

**Short:** Orders of magnitude cheaper per village once deployed — one GPU-hour vs weeks of manual GIS work.

**Technical:** Manual digitization of a village orthomosaic requires trained GIS operators for days-weeks. Automated inference runs in minutes on commodity GPU hardware. The model does not replace field verification — it prioritizes where human surveyors should focus. Our intelligence layer flags low-confidence zones for review, optimizing the human-in-the-loop workflow.

**Evidence:** Batch tiling inference; explainability review zones.

**References:** `src/intelligence/explainability.py`, `src/intelligence/survey_operations.py`

---

### Q36. What about data sovereignty and offline deployment?

**Short:** Fully offline capable — no external API calls, no cloud dependency, no data leaves the deployment environment.

**Technical:** Model weights are local files. Inference runs entirely on-premises. No telemetry, no external model APIs, no internet required after artifact deployment. Suitable for air-gapped government networks. Docker image can be transferred via secure media. Checkpoints distributed via recovery_bundle_v1.zip.

**Evidence:** No network calls in inference path; local checkpoint loading.

**References:** `src/inference/calibrated_engine.py`, `production_release/recovery_bundle_v1.zip`

---

### Q37. How do you support audit and accountability?

**Short:** SHA-256 checksums on all artifacts, provenance-stamped eval JSON, and reproducible eval scripts.

**Technical:** production_release/MANIFEST.json checksums every artifact. Eval output includes git SHA, checkpoint hashes, bias vector, and timestamp. Judges can verify integrity without trusting our slides. This is designed for government audit requirements — every metric traces to a file hash and a script.

**Evidence:** MANIFEST.json; provenance block in calibrated_eval_results.json.

**References:** `production_release/MANIFEST.json`, `run_calibrated_eval.py`, `submission/SUBMISSION_LOCK.md`

---

## SVAMITVA Relevance (Q38–Q42)

### Q38. Why is this problem important for rural India?

**Short:** Property rights depend on accurate maps. Automating infrastructure extraction from drone surveys accelerates SVAMITVA's mission to give every rural household a property card.

**Technical:** SVAMITVA maps ~6.6 lakh villages using drone orthomosaics. Manual feature extraction is the throughput bottleneck. Our system targets the three most operationally critical classes — roads (connectivity), built-up (settlement extent), water (hazards and boundaries) — directly supporting property demarcation and infrastructure planning.

**Evidence:** Operational class focus in architecture docs; survey intelligence outputs.

**References:** `docs/PROJECT_OVERVIEW.md`, `src/intelligence/survey_operations.py`

---

### Q39. What survey intelligence do you provide beyond masks?

**Short:** Road connectivity analysis, settlement fragmentation metrics, explainability review zones, and written field recommendations.

**Technical:** src/intelligence/ modules compute: spatial connectivity graphs from road masks, settlement fragmentation indices, low-confidence regions for human review, and structured survey reports with field recommendations. This transforms a segmentation model into a survey operations tool — the difference between a demo and a deployable system.

**Evidence:** survey_operations.py, spatial_analysis.py, survey_report.py modules.

**References:** `src/intelligence/`, `demo_ui/app.py`

---

### Q40. How does road detection support property surveys?

**Short:** Roads define accessibility and parcel boundaries in many villages — missing roads on maps delay property card issuance.

**Technical:** Road IoU 0.4356 with 0.64 recall means we find most roads but with boundary imprecision. Postprocessing gap-fill connects fragments. For SVAMITVA, road masks support connectivity analysis (which settlements are accessible) and serve as reference features for field teams verifying parcel boundaries.

**Evidence:** Road IoU 0.4356, recall 0.6423 in epoch_71_results.json.

**References:** `production_release/metrics/epoch_71_results.json`, `src/postprocessing.py`

---

### Q41. Why is Bridge a class if it performs poorly?

**Short:** SVAMITVA labels include bridges, but we had insufficient pixels to learn them. We train the class but do not claim Bridge performance.

**Technical:** Bridge has 6,290 GT pixels in validation vs millions for other classes. IoU is 0.0. We keep the class for schema compatibility with SVAMITVA shapefiles and postprocessing includes bridge recovery heuristics, but Bridge is explicitly listed as a non-operational class. Judges should evaluate us on Road, Built-Up, and Water.

**Evidence:** Bridge gt_pixels: 6290; IoU 0.0; documented unsupported claim.

**References:** `docs/SUBMISSION_GUIDE.md`, `docs/ARCHITECTURE.md`

---

### Q42. How would field teams use your outputs?

**Short:** GeoTIFF masks + GeoPackage vectors + a review map highlighting uncertain zones — surveyors verify flagged areas first.

**Technical:** Outputs: (1) GeoTIFF class masks importable to QGIS, (2) **GeoPackage** with layers `building_footprints`, `roads`, `water_bodies` (pyogrio export), (3) experimental `roof_type_code` on building footprints (official integers 1–4), (4) per-class area statistics, (5) explainability heatmaps and survey intelligence reports with field verification priorities. Workflow: auto-process orthomosaic → planner reviews flagged zones → field team verifies priority areas → corrected vectors feed property card generation.

**Evidence:** `src/export/vector_export.py`; Streamlit GPKG download in `demo_ui/app.py`.

**References:** `src/export/vector_export.py`, `src/intelligence/survey_report.py`, `demo_ui/app.py`, `PROJECT_BIBLE.md`

---

## Failure Analysis (Q43–Q46)

### Q43. What is your biggest weakness?

**Short:** Generalization to hard villages like NAGUL (FG 0.4124), zero Bridge detection, and experimental roof classification with limited coverage (~36% on demo tile).

**Technical:** With 6 training villages, domain shift is our primary risk. NAGUL FG is 17 points below NADALA. Bridge has insufficient training pixels. Roof classification is a second-stage ResNet18 on mask-derived footprints — many polygons are too small (&lt;32 px) for reliable crop extraction, so ~64% stay `nan` on the demo tile. We do not hide these — they are documented in demo UI and `PROJECT_BIBLE.md`. Our defense is honest reporting, per-village stress tests, and a frozen segmentation model selected by rigorous validation.

**Evidence:** NAGUL FG 0.4124; Bridge IoU 0.0; roof coverage ~186/520 on `04_fattu_bhila_building_heavy`.

**References:** `production_release/metrics/epoch_71_results.json`, `src/roof_material/crops.py`, `PROJECT_BIBLE.md`

---

### Q44. Why is Road IoU only 0.44?

**Short:** Roads are 1–3 pixels wide at 0.3 m GSD with class imbalance — the hardest class in the dataset.

**Technical:** Road IoU 0.4356, recall 0.6423, precision 0.5752. Roads are thin, fragmented, and easily confused with bare soil and paths. We tested road-precision recovery (exp06, paused) and density sampling (exp07, abandoned) without beating V1. Epoch 69 has best Road IoU (0.4397) — marginal gain. Postprocessing gap-fill helps connectivity but cannot fix all boundary errors.

**Evidence:** Road metrics; exp06 paused, exp07 gate failed; epoch 69 road 0.4397.

**References:** `production_release/reports/FINAL_MODEL_RANKING.md`, `submission/SUBMISSION_AUDIT.md`

---

### Q45. What experiments failed and what did you learn?

**Short:** SegFormer, village expansion marathon, road samplers — all rejected after measured eval against V1.

**Technical:** exp04 SegFormer: FG 0.4038 (reject). exp06 road precision: paused at ep6. exp07 density sampler: 1.32× vs 1.5× gate. exp08 CG3-DBS: NAGUL FG 0.4199. exp09 marathon: raw FG peaked ep67 at 0.5077 but regressed to 0.4493 by ep86. Lesson: more training ≠ better; architecture swaps need more data; always certify on held-out calibrated eval.

**Evidence:** All rejection metrics in SUBMISSION_AUDIT.md.

**References:** `submission/SUBMISSION_AUDIT.md`, `archive/experiment/`

---

### Q46. What happens if the model is wrong in the field?

**Short:** Human verification is mandatory — our system prioritizes review zones, it does not replace surveyors.

**Technical:** Explainability module flags uncertain regions. Survey intelligence reports recommend field verification priorities. Government workflow: model proposes, human disposes. We never claim autonomous property demarcation. Confidence scores and error maps are designed for human-in-the-loop review — standard for government geospatial AI deployment.

**Evidence:** explainability.py; unsupported claims list in SUBMISSION_GUIDE.

**References:** `src/intelligence/explainability.py`, `docs/SUBMISSION_GUIDE.md`

---

## Future Roadmap (Q47–Q50)

### Q47. What would you do with more data?

**Short:** Add diverse villages to training, especially NAGUL-like terrains, and re-certify on expanding held-out sets.

**Technical:** Priority: (1) stratified village acquisition across states/terrains, (2) maintain village-level splits, (3) active learning on low-confidence regions from deployment, (4) re-run certification matrix before any model swap. Exp09 showed that 2 extra villages without careful curriculum did not help — data diversity matters more than count.

**Evidence:** exp09 village expansion rejected; NAGUL domain shift.

**References:** `submission/IF_WE_HAD_3_MONTHS.md`, `submission/SUBMISSION_AUDIT.md`

---

### Q48. Would you add LiDAR or DSM?

**Short:** Yes — multimodal elevation would help disambiguate roads from paths and roofs from bare ground. We scoped it as exp01 but prioritized core RGB pipeline first.

**Technical:** DSM/DTM channels would feed early fusion or a second encoder branch. SVAMITVA data sometimes includes elevation derivatives. exp01_dsm_multimodal was scaffolded but not executed — the RGB-only pipeline was certified first. LiDAR is not available for all SVAMITVA villages, so RGB must remain the primary path.

**Evidence:** exp01 scaffold in archive; RGB-first deployment rationale.

**References:** `archive/experiment/exp01_dsm_multimodal/`, `submission/IF_WE_HAD_3_MONTHS.md`

---

### Q49. How would you improve Road detection specifically?

**Short:** Topology-aware loss, hard-negative mining on bare soil, and road-centric sampling — we tested these (exp06/exp07) and would iterate with more data.

**Technical:** exp06 added road FP penalty and hard negatives — paused by guardian at ep6 without beating V1. exp07 road density sampler failed 1.5× exposure gate. Next steps: centerline supervision, skeleton-based loss, wider roads via multi-scale training, and OSM pre-training where available. Road remains the highest-ROI improvement vector.

**Evidence:** exp06/exp07 rejection documented.

**References:** `archive/experiment/exp06_road_precision_recovery/`, `archive/experiment/exp07_road_density_sampler/`

---

### Q50. Is this the final system or a foundation?

**Short:** A certified foundation — frozen v1.0 for submission, designed for incremental improvement without breaking reproducibility.

**Technical:** production_release/ is immutable. Future work branches from v1.0-certified, re-runs certification matrix, and only promotes models that beat 0.4809 FG mIoU on the same protocol. The codebase supports new experiments (train.py, drift protection) but submission is locked. This is how government systems should evolve: versioned, auditable, measurable.

**Evidence:** SUBMISSION_LOCK.md; archive/experiment/ rejected alternatives.

**References:** `submission/SUBMISSION_LOCK.md`, `submission/FINAL_SUBMISSION_REVIEW.md`, `train.py`

---

## Roof Classification & Vector Export (Q51–Q55)

### Q51. Do you classify rooftops by material (RCC, Tin, Clay)?

**Short:** Partially — we output official SVAMITVA `Roof_type` **integer codes 1–4**, not material names. This is experimental, not certified like segmentation.

**Technical:** Hackathon brief lists RCC/Tin as examples. Official training shapefiles (`Built_Up_Area_typ.shp`, `Built_Up_Area_type.shp`) store `Roof_type` as integers 1–4 only — no text labels and no codebook mapping to material names ships in the repo. We trained a ResNet18 second-stage classifier on polygon crops from those shapefiles. At inference we write `roof_type_code` to the `building_footprints` GPKG layer. **Do not claim** RCC, Tin, Clay, or 95% roof accuracy — those are not evidenced in our artifacts.

**Evidence:** `Roof_type` value_counts in official shapefiles (1–4 only); `src/roof_material/classifier.py`.

**References:** `src/roof_material/`, `src/export/vector_export.py`, `PROJECT_BIBLE.md` §6

---

### Q52. Why are roof codes integers and not "Tin" or "RCC"?

**Short:** Because that is how SVAMITVA stores roof type in the official GIS — surveyors use a field-app codebook we did not receive.

**Technical:** Inventing material names from codes 1–4 would be hallucination. ArcGIS metadata references a `RoofType` domain, but domain values are not in the hackathon bundle. Our model predicts the same integer field surveyors digitize. Judges can open the GPKG in QGIS and inspect `roof_type_code` per building. If asked for material names: "We align with the official `Roof_type` attribute; material labels require the government codebook."

**Evidence:** Shapefile audit — `Roof_type` ∈ {1,2,3,4}; no RCC/Tin column in training data.

**References:** `src/roof_material/crops.py`, `submission/REQUIREMENT_COMPLIANCE_AUDIT.md` (if present)

---

### Q53. Why is roof classification coverage only ~36%?

**Short:** Most mask-derived building footprints are too small to extract a usable roof image crop — not because the model refused to classify.

**Technical:** Pipeline: segmentation mask → rooftop heuristic → polygonize → crop per polygon → ResNet18. `extract_polygon_crop()` returns `None` when the bounding window is &lt;32 px on a side. On demo tile `04_fattu_bhila_building_heavy`: 520 footprints, 186 valid crops (~35.8%), 334 `nan`. Median footprint area is tiny because heuristic polygonization fragments roofs. Improving coverage requires better footprints (full built-up blobs or survey polygons), not retraining segmentation.

**Evidence:** Measured 186/520 classified on demo tile; `min_side_px=32` in `crops.py`.

**References:** `src/roof_material/crops.py`, `src/export/vector_export.py`, `PROJECT_BIBLE.md` §6

---

### Q54. How do you export vectors for GIS workflows?

**Short:** Mask → GeoPackage with three layers: building footprints, roads, water bodies — downloadable from the Streamlit demo or via CLI.

**Technical:** `mask_to_geopackage()` polygonizes segmentation classes, writes GPKG via pyogrio (`building_footprints`, `roads`, `water_bodies`). Building layer optionally runs roof classifier when `ortho_path` and checkpoint are provided. CLI: `python scripts/export_vectors.py --tiff … --output … --device cuda`. Streamlit caches export in session state during inference to avoid re-export on every page refresh.

**Evidence:** `src/export/vector_export.py`; demo download button in `demo_ui/app.py`.

**References:** `scripts/export_vectors.py`, `demo_ui/app.py`, `PROJECT_BIBLE.md` §4

---

### Q55. Is roof classification part of your certified submission score?

**Short:** No — certified metrics are segmentation only (FG mIoU 0.4809). Roof classification is an experimental add-on we show honestly with coverage limits.

**Technical:** `run_calibrated_eval.py` and `epoch_71_results.json` certify Road, Built-Up, Water — not roof materials. Roof classifier checkpoint (`checkpoints/roof_material/best.pt`) is separate from epoch_71 segmentation. Training val metrics: ~82% accuracy, ~69% macro-F1 on held-out village crops — not comparable to segmentation IoU. Segmentation model is **frozen**; roof classifier was not retrained during demo hardening.

**Evidence:** Certified FG mIoU in `epoch_71_results.json`; roof checkpoint metadata in `best.pt`.

**References:** `production_release/metrics/epoch_71_results.json`, `checkpoints/roof_material/best.pt`, `PROJECT_BIBLE.md` §9 claim matrix

---

*End of Judge Q&A Master — 55 questions*
