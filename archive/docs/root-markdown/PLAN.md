# PLAN.md — Post-Audit Remediation Roadmap

Scope: raise the SVAMITVA Geospatial Intelligence repository from its audited state (weighted **4.8/10**) to a defensible **9+/10** across all audit categories. Every action below is tied to a concrete finding from the audit; no generic advice.

---

## Executive Summary

| Category               | Current Score | Target Score |
| ---------------------- | ------------- | ------------ |
| Repository Structure   | 5             | 9            |
| Architecture           | 6             | 9            |
| Code Quality           | 5             | 9            |
| Geospatial Correctness | 6             | 9            |
| ML Engineering         | 6             | 9            |
| Benchmark Validity     | 2             | 9            |
| Data Pipeline          | 4             | 9            |
| Production Readiness   | 4             | 9            |
| Documentation Accuracy | 3             | 9            |

**Why it currently falls short of 9+/10:** The code is real and technically literate, but the *submission* is unverifiable. The single decisive failure is benchmark integrity: every headline metric (`README.md:16-34`, `official_metrics_for_submission.md:24-41`) is sourced to `outputs/calibrated_eval_results.json`, a file that **does not exist**, alongside absent checkpoints (`outputs/checkpoints/` empty) and absent data (`data/` is `.gitkeep` only). The reported numbers cannot be regenerated, and one of them is internally contradicted (Built-Up IoU `0.1615` in README vs hardcoded baseline `0.6530` in `run_calibrated_eval.py:97`), then "explained" with a judge-deflection script (`built_up_metric_reconciliation.md:31-35`). On top of that, the official inference path has a result-affecting double-softmax bug (`calibrated_engine.py:183-191` feeding `postprocessing.py:78,123`), the production API cannot tile large orthomosaics (`production/api.py:216-224`), the ML/geospatial core has 0% test coverage, there is no CI (`.github/` absent), and documentation references methods and artifacts that do not exist (`calibrated_engine.py:16-17`).

The good news: the underlying engineering (CRS reprojection, leakage-free TIFF-level split, EMA/OHEM/Tversky training stack, hardened API, secure checkpoint loader) is sound. The gap to 9+/10 is overwhelmingly about **verifiability, reproducibility, correctness fixes, and test/CI coverage** — not a rewrite.

---

## Priority Matrix

| Priority | Issue | Severity | Expected Score Gain |
| -------- | ----- | -------- | ------------------- |
| P0 | Reported metrics unreproducible — source artifact `calibrated_eval_results.json`, checkpoints, bias, data all absent | Critical | Benchmark +6, Data +3, ML +2, Docs +3 |
| P0 | Internal metric contradiction + deflection coaching (`0.1615` vs `0.6530`) | High | Benchmark +2, Docs +2 |
| P0 | Double-softmax on official inference path | High | ML +1, Geospatial +1, Code +1 |
| P0 | Zero tests on dataset/model/training/losses/postprocessing/engine | High | Code +2, ML +1 |
| P1 | No large-orthomosaic tiling in production API | High | Production +2, Architecture +1 |
| P1 | No CI/CD (`.github/` absent) | High | Production +2, Code +1 |
| P1 | Hardcoded GSD for physical units (0.3 vs 0.2 mismatch) | Medium | Geospatial +1, Production +1 |
| P1 | Silent `except: pass` in postprocessing | Medium | Code +1, ML +0.5 |
| P1 | Misleading docstrings (`predict_tiff`/`predict_patch` do not exist) | Medium | Docs +1, Architecture +0.5 |
| P2 | Documentation/report sprawl (~40 overlapping `.md`) and stale claims | Medium | Structure +2, Docs +1 |
| P2 | print-based logging across `src/` | Medium | Production +1, Code +0.5 |
| P2 | Train/inference resolution mismatch (768 train vs 512 demo) | Medium | ML +0.5, Geospatial +0.5 |

---

# Repository Structure Improvements

### Problem
The repository root is dominated by ~40 self-generated markdown reports with overlapping scope (`judge_defense_book.md`, `repository_knockdown_list.md`, `*_remediation_report.md`, `*_validation_report.md`, `metric_inventory.md`, `metric_lineage.md`, `competitive_advantages.md`, `final_competition_narrative.md`, etc.). Several reference files that do not exist (`repository_knockdown_list.md:91` → `outputs/bridge_campaign/campaign_results.json`; `:217` → `data/quarantine/corrupt_tiffs/*`). `tools/` holds 14 experimental scripts (`bridge_impossibility_investigation.py`, `bridge_phase3_program.py`, etc.) not wired into the pipeline. This creates source-of-truth ambiguity and audit burden.

### Solution
1. Create `docs/audit-archive/` and move all historical audit/narrative/remediation reports into it (out of root), or delete the ones with no forward value.
2. Keep exactly four authoritative docs: `README.md`, `docs/ARCHITECTURE.md`, `docs/EVALUATION.md`, and one metrics file.
3. Delete or relocate dead/experimental `tools/` scripts to `experiments/` and exclude from packaging; keep only scripts referenced by the pipeline (`generate_architecture_docs.py` if used).
4. Add `LICENSE` (audit Phase: "No explicit legal license file", `repository_knockdown_list.md:141-148`).
5. Add a top-level `pyproject.toml`/package layout so `src/` is an installable package (removes `sys.path.insert` hacks in `train.py:17`, `run_calibrated_eval.py:19`, `inference_wrapper.py:17-18`).

### Files Affected
Root `*.md` (≈40 files), `tools/*`, new `LICENSE`, new `pyproject.toml`, `src/__init__.py`.

### Expected Score Impact
Repository Structure 5 → 9 (combined with packaging and removal of dead references).

---

# Architecture Improvements

## A1 — Production cannot process real orthomosaics

### Problem
`production/api.py:216-224` runs the entire uploaded image through one forward pass with no windowing. The README mission is "drone orthomosaics" — multi-GB rasters that will OOM.

### Root Cause
Tiling/accumulation logic exists only in the demo (`demo_ui/inference_wrapper.py:163-235`) and was never promoted into the shared engine; the API was wired to `CalibratedEngine.predict_batch`, which is patch-only.

### Solution
Promote the sliding-window accumulator into `CalibratedEngine` as a real `predict_large(image_or_path, patch=768, overlap=128)` method, with logit accumulation + count normalization (mirror `inference_wrapper.py:165-239`). Add a true `predict_tiff(tiff_path, out_path)` that uses `rasterio` windowed reads/writes preserving CRS + transform, so output GeoTIFF is georeferenced.

### Refactoring Strategy
1. Extract the demo's `_positions`/`_flush` accumulator into `src/inference/tiling.py`.
2. Add `CalibratedEngine.predict_large` and `predict_tiff` consuming it.
3. Re-point `production/api.py` and `demo_ui/inference_wrapper.py` to the shared implementation (single source of truth).
4. Stream tiles to bound memory; never hold the full raster decoded in RAM.

### Expected Score Impact
Architecture 6 → 9, Production +2 (shared below).

## A2 — Misleading API surface

### Problem
`calibrated_engine.py:16-17` documents `engine.predict_patch(...)` and `engine.predict_tiff(...)`; neither exists. Docstrings advertise unimplemented capabilities.

### Solution
Implement both (A1 delivers `predict_tiff`; add `predict_patch` as a thin single-image wrapper) so the docstring becomes true, with a doctest-style example that runs in CI against a synthetic input.

### Expected Score Impact
Architecture +0.5, Documentation +1.

---

# Code Quality Improvements

## C1 — Double softmax on the official inference path

### Problem
The official evaluator's postprocessing operates on doubly-softmaxed values, neutering confidence gates.

### Evidence
`calibrated_engine.py:161` produces `probs = F.softmax(biased)`, `:183` `probs_np = probs.cpu().numpy()`, `:188` `logit_acc = probs_np[b]`, passed to `postprocess_mask(mask, logit_acc)` at `:191`; inside, `refine_water`/`refine_bridges` call `_softmax(logit_acc)` again (`postprocessing.py:78,123`). The demo path correctly passes raw logits (`inference_wrapper.py:242`).

### Solution
Return raw pre-softmax ensemble logits from `_forward_ensemble` for postprocessing use; pass those (not softmax probs) into `postprocess_mask`. Keep softmax only for the probability output and argmax decision.

### Validation Method
Unit test: feed a crafted logit volume where a water region has prob 0.30 (below the 0.35 gate) and assert the gate removes it with raw logits but (incorrectly) keeps it under the double-softmax path — locking the fix.

### Expected Score Impact
Code +1, ML +1, Geospatial +1 (metrics computed via this path become trustworthy).

## C2 — Silent exception suppression

### Problem
`postprocessing.py:389-410` wraps every stage in `try/except: pass`; a broken stage is silently skipped.

### Evidence
Five bare `except Exception: pass` blocks in `postprocess_mask`.

### Solution
Replace with logged exceptions (`logger.exception(...)`) and a `strict` flag that re-raises during evaluation/CI; permissive only in the live demo. Add per-stage timing/counters.

### Validation Method
Test that injecting a forced exception in one stage raises under `strict=True` and is logged (not swallowed) under `strict=False`.

### Expected Score Impact
Code +1, ML +0.5.

## C3 — print-based observability

### Problem
`print(...)` is used across `src/` (`unified_dataset.py`, `train_one_epoch.py`, `model_factory.py`) and `tools/`.

### Solution
Introduce a `src/logging_config.py` (stdlib `logging`, structured/JSON option), replace `print` in `src/` with module loggers. Keep CLI-friendly summaries behind a `--verbose` flag.

### Validation Method
`rg "print\(" src/` returns only intentional CLI output; CI grep gate.

### Expected Score Impact
Code +0.5, Production +1 (below).

---

# Geospatial Correctness Improvements

### CRS handling
**Current Risk:** Correct today (`unified_dataset.py:334-335` reprojects SHP to raster CRS; validator enforces EPSG `[32643,32644]` at `validator.py:44,66`), but enforcement is not exercised at inference/output time, and predicted GeoTIFFs are not written with CRS (no `predict_tiff`).
**Technical Fix:** In the new `predict_tiff` (A1), copy `src.crs`/`src.transform` to the output profile so masks are georeferenced. Add an inference-time CRS assertion against the allowlist.
**Validation Procedure:** Round-trip test — open output mask with rasterio, assert `crs.to_epsg() in {32643,32644}` and `transform == input transform`.
**Expected Score Impact:** Geospatial +0.5.

### Reprojection logic
**Current Risk:** Reprojection happens per-TIFF at load; correct, but unvalidated (no test) and silently skipped if `gdf.crs is None`.
**Technical Fix:** Raise on missing source CRS in `_load_layers` (`unified_dataset.py:334`); log the source/target EPSG pair.
**Validation Procedure:** Unit test with a shapefile in EPSG:4326 reprojected to a UTM raster; assert geometry coordinates land in expected pixel windows.
**Expected Score Impact:** Geospatial +0.5.

### Raster alignment
**Current Risk:** Patch transform via `window_transform` (`:798`) is correct; but the deterministic val grid force-injects minority centroid cells (`:560-582`), making the val set partly hand-steered and potentially flattering Water (reported precision 0.9962).
**Technical Fix:** Keep guaranteed minority coverage but report two metric sets: (a) pure uniform grid, (b) grid + minority injection, clearly labeled. Never report only the injected variant as the headline.
**Validation Procedure:** Emit both metric tables in `calibrated_eval_results.json`; document which is headline.
**Expected Score Impact:** Geospatial +0.5, Benchmark +0.5.

### Orthomosaic processing
**Current Risk:** No production tiling (A1); train/inference resolution mismatch — training resizes to 768 (`config:training.image_size`), demo tiles at 512 raw (`inference_wrapper.py:45`).
**Technical Fix:** Standardize on the trained 768 patch size everywhere; set demo `PATCH_SIZE=768`. Document the GSD the model was trained at.
**Validation Procedure:** Inference-on-known-patch test: predicting a training-resolution patch reproduces the val-grid prediction within tolerance.
**Expected Score Impact:** Geospatial +0.5, ML +0.5.

### Vector topology / geometry validity
**Current Risk:** Validator detects invalid geometries (`validator.py:100`) but never repairs them; invalid polygons silently distort rasterized masks.
**Technical Fix:** Add optional `make_valid`/`buffer(0)` repair in `_load_layers` with a logged count of repaired features.
**Validation Procedure:** Feed a self-intersecting polygon; assert it is repaired and rasterizes without area explosion.
**Expected Score Impact:** Geospatial +0.5, Data +0.5.

### Coordinate integrity / spatial accuracy
**Current Risk:** Hardcoded pixel size for physical units — `village_stats.from_mask(pixel_size_m=0.3)` (`village_stats.py:89`) vs `calibrated_engine.patch_stats(pixel_size_m=0.2)` (`:196`). Area/length reports are wrong off-nominal and the two defaults disagree; `config.geospatial.default_pixel_size_m=0.3` is ignored.
**Technical Fix:** Derive GSD from the raster transform (`abs(transform.a)`), threading it through `predict_tiff`→stats. Remove hardcoded defaults; fall back to config only when no transform is available.
**Validation Procedure:** Synthetic raster with known 0.5 m GSD; assert reported `water_area_m2` equals pixel_count × 0.25.
**Expected Score Impact:** Geospatial +1, Production +1.

Net Geospatial: 6 → 9.

---

# ML Engineering Improvements

## M1 — Core is unverified (0% test coverage, unrunnable)

### Current Limitation
Coverage report covers only config/security/api/validator/evaluation; dataset, model, training loop, losses, postprocessing, and engine are **0%**. Nothing is runnable without absent data/checkpoints.

### Solution
Add a `tests/fixtures/` generator that synthesizes a tiny georeferenced GeoTIFF + matching shapefiles (in EPSG:32643) and a dummy 5-class checkpoint, enabling end-to-end tests on CPU.

### Implementation Plan
1. `tests/conftest.py`: build a 1024×1024 synthetic UTM raster + Road/Bridge/Built-Up/Water shapefiles with `rasterio`/`geopandas`.
2. Save a randomly-initialized DeepLabV3+ checkpoint with the exact `config`/`model_state_dict`/`ema_state_dict` keys `from_checkpoints` expects (`calibrated_engine.py:90-105`).
3. Tests: dataset patch shape/dtype, rasterization priority (Road wins overlap), loss finiteness/gradients, EMA update, engine `predict_batch`/`predict_large` shape, evaluator metric math against hand-computed values.

### Validation Strategy
`pytest --cov` ≥ 85% on `src/` (not just the 5 modules today); CI gate on coverage.

### Expected Score Impact
ML +1, Code +2.

## M2 — Calibration/bias is unverifiable

### Current Limitation
`optimal_bias.json` is absent; engine silently falls back to `_DEFAULT_BIAS=[0,1.5,4.0,0,0]` (`calibrated_engine.py:108-116`), so "calibration enabled" claims are not backed by an artifact.

### Solution
Ship `outputs/optimal_bias.json` (or regenerate via `bias_search.py`) and record the bias actually used inside `calibrated_eval_results.json`. Log a warning-level message when fallback bias is used, and make the official eval **fail** if the bias file is missing (no silent fallback in scoring mode).

### Validation Strategy
Eval refuses to emit "calibration: yes" unless the bias file loaded successfully.

### Expected Score Impact
ML +0.5, Benchmark +0.5.

## M3 — Augmentation/imbalance claims need evidence
### Current Limitation
Bridge copy-paste, minority-aware sampling, OHEM, Tversky, conditional Dice are implemented (`unified_dataset.py:590-664`, `multiclass_loss.py`) but Bridge IoU is still 0.0 — i.e., the imbalance machinery demonstrably does not work for Bridge.
### Solution
Either (a) honestly retain Bridge as non-operational and remove unused bridge knobs from the default path, or (b) run an ablation proving each component's marginal contribution and publish it. Do not ship inert complexity.
### Validation Strategy
Ablation table (baseline vs +OHEM vs +Tversky vs +copy-paste) checked into `docs/EVALUATION.md`, regenerated by script.
### Expected Score Impact
ML +0.5, Benchmark +0.5.

Net ML: 6 → 9 (the remaining +1 comes from C1 double-softmax fix and resolution alignment).

---

# Benchmark Credibility Improvements

## B1 — Metrics are unreproducible (the decisive failure)

### Problem
No checkpoints, no data, no bias, no eval artifact; every number lives only in markdown.

### Evidence
`official_metrics_for_submission.md:9-13` cites `outputs/calibrated_eval_results.json` (absent). `outputs/checkpoints/` empty; `data/` is `.gitkeep`; `.gitignore:12-47` blocks all of them. `run_calibrated_eval.py:62-67` loads paths that do not exist.

### Solution
1. Publish artifacts out-of-band (Git LFS / release assets / cloud bucket): `best_model.pth`, `latest_model.pth`, `optimal_bias.json`, and either the licensed validation rasters or a small redistributable validation subset.
2. Provide `scripts/fetch_artifacts.sh` to download them into `outputs/`/`data/`.
3. Make `run_calibrated_eval.py` write a complete provenance block into `calibrated_eval_results.json`: git SHA, checkpoint SHA-256 (use `file_sha256` already in `checkpoints.py:14`), bias values, split definition, library versions, timestamp.
4. Commit the regenerated `calibrated_eval_results.json` so README numbers trace to a real file.

### Reproducibility Plan
`make reproduce` → fetch artifacts → run eval → regenerate metrics doc → diff against committed JSON; CI runs this on the synthetic fixture to prove the path executes.

### Expected Score Impact
Benchmark +6, Data +3, Documentation +3.

## B2 — Internal contradiction + deflection

### Problem
Built-Up IoU `0.1615` (README/official) contradicts hardcoded `0.6530` baseline; a "Judge-Safe Statement" coaches deflection.

### Evidence
`README.md:27`, `official_metrics_for_submission.md:33` vs `run_calibrated_eval.py:97`; `built_up_metric_reconciliation.md:31-35`.

### Solution
Remove all hardcoded comparator literals from `run_calibrated_eval.py:94,97`; compute the baseline (no-postprocess pass) at runtime in the same script so "baseline" and "calibrated" come from one execution. Delete the deflection language; replace with the regenerated provenance table.

### Reproducibility Plan
Single script emits baseline + calibrated columns from one run; no literals anywhere.

### Expected Score Impact
Benchmark +2, Documentation +2.

## B3 — Evaluation transparency
### Problem
Validation uses only 2 TIFFs with hand-injected minority patches; no cross-validation or confidence interval.
### Solution
Report per-TIFF breakdown, both grid variants (see Geospatial), and (resources permitting) k-fold over available TIFFs. Document the exact split in `docs/EVALUATION.md`.
### Expected Score Impact
Benchmark +0.5.

Net Benchmark: 2 → 9.

---

# Data Pipeline Improvements

### Current Problem
Hardcoded absent source paths (`unified_dataset.py:118-137` → `data/Raz/...`), no shipped data, and the validator/manifest describe an unexecutable state (`data_manifest.md`, `data_governance_validation_report.md`).

### Solution
1. Make dataset roots config-driven (already partially in `config/platform_config.v1.json`); move `DEFAULT_SOURCES` paths into config so no path is hardcoded in code.
2. Ship the synthetic fixture (M1) so the pipeline + validator run in CI with zero external data.
3. Wire `DatasetValidator.run()` as a **gating preflight** in `train.py` and `run_calibrated_eval.py` (fail fast on missing/corrupt assets, missing CRS, invalid geometry) — it currently exists (`validator.py`) but is not invoked by the entry points.
4. Add a manifest generator that records per-TIFF CRS, GSD, bounds, feature counts, and SHA-256, written to `data/manifest.json`.

### Validation
CI runs `DatasetValidator` on the fixture and asserts `ok=True`; a deliberately corrupted fixture asserts `ok=False` with the right severity.

### Expected Score Impact
Data 4 → 9 (combined with B1 artifacts and geometry-repair).

---

# Production Readiness Improvements

## P1 — No tiling/scalability
### Problem
`production/api.py:216-224` no windowing; OOM on real orthomosaics.
### Solution
Route `/infer` and `/infer-batch` through `CalibratedEngine.predict_large` (A1); add a `/infer-tiff` endpoint returning a georeferenced mask via `predict_tiff`.
### Deployment Impact
Handles arbitrarily large rasters within bounded memory.
### Expected Score Impact
Production +2.

## P2 — No CI/CD
### Problem
`.github/` absent — no automated gates.
### Solution
Add `.github/workflows/ci.yml`: lint (ruff/black), type-check (mypy on `src/`), `pytest --cov` (≥85%), security scan (pip-audit), build the Docker image, and run the synthetic reproduce path. Add a release workflow that publishes artifacts + checksums.
### Deployment Impact
Every PR is quality-gated; reproducibility is continuously proven.
### Expected Score Impact
Production +2, Code +1.

## P3 — Observability/logging
### Problem
print-based logging (C3); `/metrics` returns only request count + uptime (`api.py:200-205`); request counter is a mutable global (`:39,213-214`).
### Solution
Structured logging; expose Prometheus-style metrics (latency histogram, per-class pixel counts, error counts); replace global counter with a thread-safe metrics registry.
### Deployment Impact
Real incident diagnosis.
### Expected Score Impact
Production +1.

## P4 — Packaging/env fragility
### Problem
Dockerfile base is `python:3.11-slim` while the venv is 3.10; `rasterio/fiona/geopandas` in slim depend on manylinux wheels and are untested in-container (`container_validation_report.md` describes, doesn't prove).
### Solution
Pin Docker to `python:3.10-slim` to match the tested runtime; add a CI job that builds the image and runs a smoke `pytest` inside it; consider a GDAL base image if wheel install proves fragile.
### Deployment Impact
Eliminates environment drift between dev and container.
### Expected Score Impact
Production +1.

Net Production: 4 → 9.

---

# Documentation Corrections

## README Corrections

1. **Metric provenance**
   - Current claim (`README.md:38-44`): metrics traced to `outputs/calibrated_eval_results.json` + checkpoints + `optimal_bias.json`.
   - Actual implementation: none of these files exist in the repo.
   - Corrected wording: "Metrics are reproduced by `make reproduce`, which downloads released checkpoints (SHA-256 listed) and regenerates `outputs/calibrated_eval_results.json` (committed). Run `scripts/fetch_artifacts.sh` first."

2. **Built-Up IoU consistency**
   - Current claim: README Built-Up IoU `0.1615` while `run_calibrated_eval.py:97` baseline says `0.6530`.
   - Actual implementation: baseline literal is hardcoded and contradicts the headline.
   - Corrected wording: present baseline and calibrated columns from a single computed run; remove literals.

3. **Engine API**
   - Current claim (`calibrated_engine.py:16-17`): `predict_patch` / `predict_tiff` usage examples.
   - Actual implementation: methods do not exist.
   - Corrected wording: only after A1/A2 implement them; otherwise remove the examples.

4. **End-to-end orthomosaic inference**
   - Current claim (`README.md:3`): "end-to-end geospatial AI pipeline ... on drone orthomosaics."
   - Actual implementation: production API has no tiling; only the demo tiles.
   - Corrected wording: accurate only after P1; until then state "patch-level inference; orthomosaic tiling available in the demo."

5. **Patch size / split description**
   - Current claim (`README.md:43`, `official_metrics_for_submission.md:13`): "512-patch validation grid."
   - Actual implementation: `config:evaluation.max_val_patches=500` and `unified_dataset.py:553` caps at 500; training `image_size=768`.
   - Corrected wording: "≤500-patch deterministic 768px val grid over 2 TIFFs (+ guaranteed minority patches)."

6. **Calibration enabled**
   - Current claim: "Calibration status: Enabled (`outputs/optimal_bias.json`)."
   - Actual implementation: file absent → engine uses `_DEFAULT_BIAS` fallback.
   - Corrected wording: state the actual bias vector used, sourced from the shipped JSON.

---

# High-Impact 30-Day Roadmap

## Week 1 — Make it true and verifiable (P0)
Tasks:
- Publish + fetch script for checkpoints, `optimal_bias.json`, validation data; commit regenerated `calibrated_eval_results.json` with full provenance (git SHA, checkpoint SHA-256, bias, versions).
- Fix double-softmax (C1); remove hardcoded baseline literals (`run_calibrated_eval.py:94,97`) and compute baseline at runtime; delete deflection text in `built_up_metric_reconciliation.md`.
- Correct README/metrics docs to match reality.
Expected gains: Benchmark 2→8, Documentation 3→7, ML 6→7, Code 5→6.

## Week 2 — Prove it with tests + CI (P0/P1)
Tasks:
- Synthetic fixture generator (raster + shapefiles + dummy checkpoint); end-to-end CPU tests for dataset/losses/EMA/engine/evaluator; coverage ≥85% on `src/`.
- Add `.github/workflows/ci.yml` (lint, mypy, pytest+cov, pip-audit, docker build, synthetic reproduce).
- Replace `except: pass` with logged/strict handling (C2).
Expected gains: Code 6→9, Production 4→6, ML 7→8, Data 4→6.

## Week 3 — Scale + geospatial correctness (P1)
Tasks:
- Extract shared tiling (`src/inference/tiling.py`); implement `predict_large`/`predict_tiff` with CRS-preserving GeoTIFF output; re-point API + demo; add `/infer-tiff`.
- Derive GSD from raster transform; remove hardcoded 0.3/0.2; thread through stats.
- Geometry repair + CRS assertions in loader; wire `DatasetValidator` as preflight in entry points.
Expected gains: Architecture 6→9, Production 6→8, Geospatial 6→9, Data 6→8.

## Week 4 — Hardening, observability, cleanup (P1/P2)
Tasks:
- Structured logging across `src/`; Prometheus metrics; thread-safe counters; Docker base → 3.10 + in-container smoke test.
- Repo cleanup: archive ~40 reports to `docs/audit-archive/`, remove dead `tools/` scripts, add `LICENSE` + `pyproject.toml` packaging (drop `sys.path` hacks).
- Publish ablation table proving each ML component's contribution (or remove inert bridge knobs).
Expected gains: Production 8→9, Repository Structure 5→9, Documentation 7→9, ML 8→9, Benchmark 8→9.

---

# Target State

After remediation the repository is a single installable package (`pip install -e .`) with a clean root (README + 3 docs + `src/` + `tests/` + `.github/`). `make reproduce` downloads released, checksummed checkpoints and validation data and regenerates `outputs/calibrated_eval_results.json`, whose every number matches the README, derived from one execution that also computes the no-postprocess baseline (no hardcoded literals). The inference engine has one shared, tested tiling implementation used by both the demo and the production API; `predict_tiff` writes CRS-preserving GeoTIFFs; physical units come from the raster's real GSD. Postprocessing uses raw logits (no double softmax) and raises on failure under `strict` mode. CI gates every PR with lint, types, ≥85% coverage on `src/`, security scan, Docker build, and a synthetic end-to-end reproduce. The dataset validator runs as a preflight and the pipeline executes against a committed synthetic fixture with zero external dependencies. Bridge is either ablation-justified or honestly retained as non-operational with the dead knobs removed.

---

# Projected Audit Scores After Remediation

| Category | Current | Projected |
| -------- | ------- | --------- |
| Repository Structure | 5 | 9 |
| Architecture | 6 | 9 |
| Code Quality | 5 | 9 |
| Geospatial Correctness | 6 | 9 |
| ML Engineering | 6 | 9 |
| Benchmark Validity | 2 | 9 |
| Data Pipeline | 4 | 9 |
| Production Readiness | 4 | 9 |
| Documentation Accuracy | 3 | 9 |

Weighted projected overall ≈ **9.0/10** (same weights as the audit: Geospatial 0.20, ML 0.20, Benchmark 0.15, Architecture 0.10, Code 0.10, Data 0.10, Structure 0.05, Production 0.05, Docs 0.05).

---

# Final Assessment

1. **Three highest-leverage changes:** (a) Ship checkpoints + bias + validation data and commit a provenance-stamped `calibrated_eval_results.json` so every metric reproduces (B1); (b) add the synthetic fixture + tests + CI that prove the core runs (M1/P2); (c) fix the double-softmax and remove hardcoded/contradictory baselines (C1/B2).

2. **Biggest technical blocker:** Reproducibility. Nothing — not eval, not the API, not the tests — can run end-to-end because checkpoints and data are absent and gitignored (`.gitignore:12-47`, empty `outputs/checkpoints/`). Until artifacts are published, no other improvement can be verified.

3. **Biggest geospatial weakness:** Physical-unit integrity — hardcoded GSD (`village_stats.py:89` = 0.3 vs `calibrated_engine.py:196` = 0.2) instead of the raster transform, plus no CRS-preserving georeferenced output (no `predict_tiff`). Spatial *code* is correct; spatial *outputs* are not trustworthy.

4. **Biggest engineering weakness:** Verification debt — 0% test coverage on dataset/model/training/losses/postprocessing/engine and no CI, so a real correctness bug (double softmax) shipped on the official path undetected.

5. **What must be fixed first to reach 9+/10:** Benchmark Validity (currently 2). Publish artifacts, make `run_calibrated_eval.py` regenerate a committed, provenance-stamped results file from a single run, eliminate the metric contradiction and deflection text, and fix the double-softmax so the regenerated numbers are correct. Everything else is gated on this becoming reproducible.
