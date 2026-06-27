# Score Maximization Plan

**Context:** Repository frozen except high-impact changes. Deadline approaching. Engineering, judge experience, documentation, and reproducibility frameworks are already above average.

**Objective:** Maximize **final judge score** — not audit score, not GitHub quality.

**Date:** 2026-06-15

---

## Phase 1 — Score Decomposition

Estimated weights reflect a **geospatial AI hackathon** judged by senior engineers with **≤15 minutes per submission**. Scores are **0–10** per dimension.

| Dimension | Est. Weight | Current Score | Max Achievable | Justification |
|-----------|-------------|---------------|----------------|---------------|
| **AI performance** | **22%** | **4.5** | **9.0** | Primary differentiator in ML hackathons. Judges open `evidence/judge_package/index.html` and see **FG mIoU 0.1989** on synthetic data. Road/Water IoU 0.0. Archived production claim **0.3871** is not clone-verifiable. Competitors with verified real-data mIoU 0.35–0.45 score 7–9 here. |
| **Benchmark credibility / trust** | **18%** | **5.5** | **9.5** | Judges penalize metrics they cannot reproduce. Provenance chain exists but production artifacts are external (`SVAMITVA_ARTIFACTS_URL` unset). Synthetic-only verification reads as "pipeline works, results unproven." |
| **Geospatial intelligence** | **12%** | **8.0** | **9.0** | CRS reprojection, GSD from transform, shapefile rasterization, GeoTIFF tiling API. Strong; marginal room left without real village demo data in-repo. |
| **Real-world impact** | **12%** | **7.0** | **9.0** | Survey intelligence (`build_survey_intelligence`), recommendations, `/survey-report` API. Value narrative is compelling but **not demonstrated on real NADALA/NAGUL orthomosaics** in submission. |
| **Technical innovation** | **10%** | **7.5** | **8.5** | Ensemble + bias calibration + postprocessing + decision-support layer. Not novel enough to offset weak headline mIoU. |
| **Demonstration quality** | **10%** | **8.5** | **9.5** | HTML evidence pack, 6 overlays, SHA-256 manifest, `make judge`, Streamlit verification page. Near ceiling. |
| **Reproducibility** | **8%** | **8.0** | **9.5** | CI, `reproduce.sh`, provenance JSON. Gap is production path requires manual tarball fetch. |
| **Engineering quality** | **5%** | **8.5** | **9.0** | Tests (64% coverage), secure checkpoints, FastAPI, Docker. Above average; low marginal return. |
| **Presentation** | **3%** | **8.0** | **9.0** | README judge quick start, `JUDGE_EXPERIENCE.md`. Sufficient; polish yields tiny gains. |

**Weighted current score:**  
`0.22×4.5 + 0.18×5.5 + 0.12×8.0 + 0.12×7.0 + 0.10×7.5 + 0.10×8.5 + 0.08×8.0 + 0.05×8.5 + 0.03×8.0` ≈ **6.7 / 10**

**Weighted max (with production bundle, no new training):** ≈ **8.6 / 10**

**Weighted max (with full retrain + bundle):** ≈ **8.9 / 10** (uncertain, deadline-risky)

---

## Phase 2 — The Bottleneck (One Factor)

**Unverifiable production AI performance.**

**Evidence:**

1. Judge-first artifact (`evidence/judge_package/metrics.json`) reports **FG mIoU 0.1989** — the number judges actually see.
2. `data/` is empty (`.gitkeep` only); production checkpoints are gitignored; `SVAMITVA_ARTIFACTS_URL` has no default URL.
3. Archived metrics (`docs/audit-archive/judge_safe_metrics_package.md`) claim **FG mIoU 0.3871** on real validation villages — **+93% relative** over what judges can verify — but cannot be reproduced from the submission.
4. AI performance dimension (22% weight) scores **4.5/10** — the largest weighted deficit: `0.22 × (9.0 − 4.5) = 0.99` points on the composite vs a verified production benchmark.

No other dimension has a weighted gap this large. Engineering (5% weight, gap 0.5) and demonstration (10% weight, gap 1.0) are already near ceiling.

---

## Phase 3 — ROI Analysis

`Expected Value = Estimated Score Gain × Probability of Success`

| Improvement | Est. Score Gain (composite) | Effort | P(success) | EV | Rank |
|-------------|----------------------------|--------|------------|-----|------|
| **Host production benchmark tarball + README link** | **+1.2 to +1.6** | 4–8 hrs | **0.85** | **1.14** | **1** |
| Embed production metrics panel in judge HTML (from real eval) | +0.3 to +0.5 | 2–3 hrs | 0.90 | 0.36 | 2 |
| 3-minute live demo script (real ortho inference) | +0.2 to +0.4 | 3–4 hrs | 0.80 | 0.24 | 3 |
| Full production retrain (80 epochs, 6 villages) | +0.3 to +0.8 | 40–80 hrs | 0.35 | 0.21 | 4 |
| Architecture swap (SegFormer, etc.) | +0.2 to +0.6 | 60+ hrs | 0.25 | 0.10 | 5 |
| More synthetic training epochs | +0.05 to +0.15 | 4–8 hrs | 0.70 | 0.07 | 6 |
| Hosted cloud demo URL | +0.15 to +0.25 | 8–16 hrs | 0.60 | 0.12 | 7 |
| Additional documentation / audit reports | −0.1 to +0.05 | 4+ hrs | 0.50 | negative | reject |
| Bridge class recovery | −0.2 to +0.1 | 20+ hrs | 0.20 | negative | reject |
| UI polish / new Streamlit pages | +0.05 to +0.10 | 8+ hrs | 0.80 | 0.06 | reject |

**Rejected (low EV):** architecture changes, bridge campaign, more docs, synthetic-only training, cosmetic UI.

---

## Phase 4 — Winning Strategy

**Selected: B — Improve benchmark credibility**

| Strategy | Expected Composite Gain | Rationale |
|----------|------------------------|-----------|
| A. Model performance | +0.2–0.8 (uncertain) | Requires `data/` + 40–80 GPU-hours; high deadline risk; checkpoints may already exist from prior training |
| **B. Benchmark credibility** | **+1.2–1.6** | Uses **existing** trained weights; converts archived 0.3871 from claim → verified fact; highest EV |
| C. Judge perception | +0.1–0.2 | Mostly done (`make judge`, HTML pack); diminishing returns |
| D. Practical impact | +0.2–0.4 | Needs real ortho outputs in evidence; dependent on B anyway |
| E. Novelty | +0.1–0.2 | Intelligence layer already shipped; cannot overcome mIoU gap alone |

**Quantitative justification:**  
Benchmark credibility directly lifts **two** high-weight dimensions:

- AI performance: 4.5 → 7.5 (+3.0 × 22% = **+0.66**)
- Trust: 5.5 → 9.0 (+3.5 × 18% = **+0.63**)

**Total: +1.29 composite points** with 85% success probability if authorized artifacts exist locally.

Strategy A adds similar upside only if retraining beats existing checkpoints — unlikely in one week without dedicated GPU farm and frozen hyperparameters already tuned over 80 epochs.

---

## Phase 5 — Highest-ROI Actions

### Do (in order)

| # | Action | Time | Est. Gain | Dependency |
|---|--------|------|-----------|------------|
| 1 | Locate production `best_model.pth`, `latest_model.pth`, `optimal_bias.json` from prior training run | 1 hr | — | Local disk / team storage |
| 2 | Confirm hackathon redistribution rights for checkpoints + 1–2 validation orthomosaics | 2 hr | — | Organizer approval |
| 3 | Run `bash scripts/package_production_release.sh` → tarball + `benchmark/ARTIFACT_MANIFEST.json` | 1 hr | +0.8 | Step 1–2 |
| 4 | Host tarball (GitHub Release / Google Drive / institute server); set `SVAMITVA_ARTIFACTS_URL` in README | 2 hr | +0.4 | Step 3 |
| 5 | Run production eval; commit `outputs/calibrated_eval_results.json` with real FG mIoU | 1 hr | +0.3 | Step 4 |
| 6 | Add **production metrics panel** to `evidence/judge_package/index.html` (regenerated, not hand-edited) | 2 hr | +0.2 | Step 5 |
| 7 | Write **3-minute judge demo script**: fetch → verify → open HTML → show real overlay | 2 hr | +0.2 | Step 6 |

**Total engineering time:** 11–13 hours  
**Expected composite gain:** +1.2 to +1.6 (6.7 → **7.9–8.3**)

### Ignore

- New ML architectures
- Bridge recovery
- Additional markdown audit reports
- Synthetic-only training improvements
- CI/test coverage expansion
- Refactoring production API
- New intelligence features

### Risks

| Risk | Mitigation |
|------|------------|
| Redistribution not permitted | Request expedited organizer approval; offer checksum-only manifest + private judge link |
| Checkpoints lost | Only path left is emergency retrain (low P(success)); escalate immediately |
| Tarball too large for judges | Ship validation subset (2 villages) + checkpoints only (~2–5 GB) |
| Judges skip fetch step | Pre-commit production `calibrated_eval_results.json` + production panel in HTML with SHA-256 proof |

---

## Phase 6 — Model Performance Investigation

**Can segmentation performance be materially improved before deadline?**

| Lever | Realistic Gain | Time | Verdict |
|-------|----------------|------|---------|
| **Data quality** | +0.05–0.15 mIoU | 8–16 hrs curation | Needs `data/` access; not in repo |
| **Augmentation** | +0.02–0.08 mIoU | 4–8 hrs | Already has bridge copy-paste; marginal |
| **Architecture** | +0.05–0.15 mIoU | 40+ hrs | High risk; breaks checkpoint compatibility |
| **Calibration (bias search)** | +0.01–0.04 mIoU | 2–4 hrs | Already tuned for production |
| **Post-processing** | +0.01–0.03 mIoU | 2–4 hrs | Pipeline complete; delta already in eval |
| **Class imbalance** | +0.03–0.10 mIoU | 8–16 hrs | Requires retrain |
| **Full retrain (80 epochs)** | +0.00–0.10 vs existing | 40–80 GPU-hrs | May **not beat** epoch-43/80 ensemble already archived |

**Realistic estimate:** Without existing checkpoints, full retrain might reach FG mIoU **0.30–0.40** (based on archived 0.3871). With existing checkpoints, **0.38±0.03** is the ceiling without weeks of experimentation.

**Conclusion:** Retraining is **not** the highest-ROI path. **Publishing existing production artifacts** dominates.

---

## Phase 7 — If Performance Cannot Be Improved

Alternative strengths that **partially** offset weaker metrics:

| Strength | Realistic offset | Example |
|----------|------------------|---------|
| Survey intelligence narrative | +0.2–0.3 composite | "We don't just segment — we produce village access reports" |
| Geospatial engineering depth | +0.1–0.2 | CRS-correct tiling on 10k×10k orthomosaics |
| Honest bridge governance | +0.05 | Reduces skepticism; doesn't win |
| One-command verification | +0.1 | Judges trust process even if mIoU is mid-tier |

**These cannot outweigh a 0.20 vs 0.40 mIoU gap** against data-rich competitors. They are **supporting arguments**, not a winning strategy alone.

---

## Phase 8 — Final Decision

### If technical lead with one week remaining, invest every hour in:

**One objective:** Make production FG mIoU (~0.39 on real validation orthomosaics) **independently verifiable by judges in one command.**

### Exact deliverables

1. `benchmark/svamitva_production_benchmark.tar.gz` — checkpoints + `optimal_bias.json` + 1–2 validation village orthomosaics/shapefiles
2. `benchmark/ARTIFACT_MANIFEST.json` — SHA-256 checksums for every artifact
3. Public `SVAMITVA_ARTIFACTS_URL` in README (first line of judge section)
4. Committed `outputs/calibrated_eval_results.json` from production eval (provenance intact)
5. Regenerated `evidence/judge_package/index.html` with **production metrics panel** alongside synthetic verification
6. `DEMO_SCRIPT.md` — 3-minute spoken walkthrough for judges

### Expected score gain

**+1.2 to +1.6 composite points** (6.7 → 7.9–8.3), moving from upper-middle tier to **credible top-quartile contender**.

### Why all other options are inferior

- **Model retraining:** 40–80 GPU-hours, may not exceed existing epoch-43/80 checkpoints, misses deadline.
- **Judge perception / docs:** Already at 8+/10; +0.1 ceiling.
- **Novelty features:** Judges score ML hackathons on **proven accuracy on real geodata** first.
- **Synthetic improvements:** Caps at ~0.25 mIoU; judges will still compare unfavorably to 0.40+ teams.

**Commit to benchmark credibility. Ship the production bundle. Everything else is distraction.**
