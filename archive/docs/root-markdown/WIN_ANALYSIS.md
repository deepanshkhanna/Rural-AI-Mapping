# Win Probability Analysis — Judge Dimension Scoring

**Assessment date:** 2026-06-15  
**Post-remediation position:** Strong Contender (engineering) / Benchmark credibility gap (scoring)

This document reverse-engineers likely judge scoring across eight dimensions, estimates current vs maximum achievable scores, and identifies gaps. Scores are on a **0–10** scale per dimension.

---

## Scoring Model

| # | Dimension | Weight (est.) | What judges actually inspect |
|---|-----------|---------------|------------------------------|
| 1 | Technical depth | 15% | Architecture, tiling, CRS, ensemble, loss, API |
| 2 | Geospatial correctness | 15% | EPSG handling, GSD, shapefile rasterization, GeoTIFF I/O |
| 3 | Innovation | 10% | Survey intelligence, explainability, decision support |
| 4 | Practical usefulness | 15% | Village survey report, recommendations, deployable API |
| 5 | Reproducibility | 15% | One-command verify, CI, provenance JSON, SHA-256 |
| 6 | Demonstration quality | 10% | HTML evidence pack, Streamlit, overlays |
| 7 | Trustworthiness | 15% | Metrics match artifacts, no contradictions, honest bridge status |
| 8 | Real-world deployability | 5% | Docker, FastAPI, security, production config |

---

## Dimension Scores

| Dimension | Current | Max Achievable | Gap | Notes |
|-----------|---------|----------------|-----|-------|
| Technical depth | **8.5** | 9.5 | 1.0 | DeepLab ensemble, tiling, calibrated pipeline, intelligence layer. Gap: no novel architecture paper-level contribution. |
| Geospatial correctness | **8.0** | 9.0 | 1.0 | CRS reprojection, repair, GSD from transform, georeferenced output. Gap: limited real-world CRS diversity in bundled data. |
| Innovation | **7.5** | 8.5 | 1.0 | Survey intelligence + explainability beyond pure segmentation. Gap: not unique if competitors also ship GIS dashboards. |
| Practical usefulness | **8.0** | 9.0 | 1.0 | `/survey-report`, recommendations, fragmentation metrics. Gap: value unproven on real village orthomosaics in-repo. |
| Reproducibility | **8.0** | 9.5 | 1.5 | `make judge`, CI, `reproduce.sh`, provenance chain. Gap: production checkpoints external. |
| Demonstration quality | **8.5** | 9.5 | 1.0 | Self-contained HTML, 6 overlay panels, manifest. Gap: synthetic mIoU modest on multi-class. |
| Trustworthiness | **6.5** | 9.5 | **3.0** | Contradictions removed; synthetic metrics now reproducible. **Production headline mIoU (0.3871) not verifiable from clone.** |
| Real-world deployability | **7.5** | 8.5 | 1.0 | API, Docker, secure checkpoints. Gap: no hosted demo URL. |

**Weighted composite (current):** ~**7.6 / 10**  
**Weighted composite (max without external data):** ~**8.8 / 10**

---

## Primary Competitive Failure Mode

Judges with limited time will:

1. Open `evidence/judge_package/index.html` → see **synthetic FG mIoU ~0.20**, Built-Up IoU ~0.80
2. Compare to teams showing **verified production mIoU 0.35–0.45** on real orthomosaics
3. Conclude: *engineering is solid; benchmark leadership is unproven*

Engineering quality is no longer the bottleneck. **Verifiable production metrics** are.

---

## Phase 2 — Top 5 ROI Improvements

All candidates scored; only top five retained.

| Improvement | Judge Impact | Technical Impact | Credibility Impact | Effort | Retain? |
|-------------|--------------|------------------|--------------------|--------|---------|
| **1. One-command judge workflow (`make judge`)** | High | Low | High | Low | ✅ |
| **2. Fix synthetic bias bug (zero bias on synthetic path)** | High | Medium | **Very High** | Low | ✅ |
| **3. Full-raster verification metrics in evidence pack** | High | Low | High | Low | ✅ |
| **4. Production benchmark release framework (manifest + verify scripts)** | Medium | Medium | **Very High** | Medium | ✅ |
| **5. Pre-generated committed judge package with honest metrics** | High | Low | High | Low | ✅ |
| New ML architecture (SegFormer, etc.) | Medium | High | Low | **Very High** | ❌ |
| Bridge class recovery campaign | Low | High | Negative (overclaim risk) | High | ❌ |
| More audit markdown reports | Negative | None | Negative | Medium | ❌ |
| Hosted cloud demo | High | Low | Medium | High | ❌ (deferred) |
| Bundle 200MB checkpoints in git | Medium | None | High | Medium | ❌ (legal/size; use release tarball) |

### Selected Top 5 (implemented)

1. `scripts/judge_verify.sh` + `make judge`
2. Synthetic zero-bias in `build_synthetic_fixtures.py`
3. Full-raster scoring in `generate_judge_package.py`
4. `benchmark/ARTIFACT_MANIFEST.template.json`, `verify_production_benchmark.sh`, `package_production_release.sh`
5. Regenerated `evidence/judge_package/` with FG mIoU **0.1989**, Built-Up IoU **0.7955**

---

## Phase 4 — Production Artifacts Investigation

| Question | Answer |
|----------|--------|
| Can production artifacts be legally included? | **Conditionally.** SVAMITVA orthomosaics and trained weights may be hackathon-licensed; redistribution requires organizer approval. Cannot assume in-repo without explicit permission. |
| Can metrics be regenerated? | **Yes**, if checkpoints + `data/` + `optimal_bias.json` are provided via `SVAMITVA_ARTIFACTS_URL`. Pipeline is complete (`run_calibrated_eval.py`). |
| Can a reproducible benchmark package be built? | **Yes.** `scripts/package_production_release.sh` creates tarball + SHA-256 manifest. |
| Can a judge reproduce headline results locally? | **Only after fetching release tarball.** Not from clone alone. |
| Can verification be one command? | **Yes for synthetic:** `make judge`. **Yes for production:** fetch + eval + `verify_production_benchmark.sh`. |

---

## Phase 6 — Competitor Analysis

### Unique advantages this repository retains

| Advantage | Can it outweigh higher mIoU? |
|-----------|------------------------------|
| End-to-end **survey intelligence** (access, fragmentation, water proximity) | Partially — if judges weight decision support |
| **Cryptographic provenance** (SHA-256 manifest, git SHA in eval JSON) | Partially — builds trust, not raw accuracy |
| **Honest bridge governance** (explicit non-operational) | Small positive — reduces skepticism |
| **Geospatial engineering depth** (CRS, tiling, GeoTIFF API) | Partially — differentiates vs notebook-only teams |
| **One-command judge verification** | Moderate — reduces friction |

### What is missing

**Verifiable production-scale segmentation metrics bundled with the submission.** Teams with mIoU 0.40+ on real data will rank higher on the dimension judges weight most heavily unless this gap is closed via an authorized release artifact.

---

## Evidence Generated (this phase)

| Artifact | Value |
|----------|-------|
| `evidence/judge_package/metrics.json` | FG mIoU 0.1989 (synthetic, full raster) |
| `outputs/calibrated_eval_results.json` | FG mIoU 0.2007 (16-patch val grid) |
| `evidence/judge_package/verification_manifest.json` | SHA-256 chain |
| `benchmark/ARTIFACT_MANIFEST.template.json` | Production release template |

---

*See `JUDGE_EXPERIENCE.md` for judge workflow and `WIN_PROBABILITY_REPORT.md` for final verdict.*
