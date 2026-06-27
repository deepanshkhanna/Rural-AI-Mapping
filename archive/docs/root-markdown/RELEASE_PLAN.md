# Release Plan — 5-Day Submission Sprint

**Role:** Technical Lead / Release Manager  
**Deadline:** ~5 days  
**Position:** Strong Contender — engineering and judge experience above average; **benchmark credibility** is the largest remaining score opportunity.

**Operating principle:** Submission stability > experimental upside.

---

## Phase 1 — Release Readiness Assessment

| Area | Status | Risk | Notes |
|------|--------|------|-------|
| **Demo** | **Yellow** | Medium | Streamlit + `CalibratedEngine` work with local checkpoints. `data/` empty — production village demo requires fetched artifacts. Synthetic path functional. |
| **Judge Package** | **Green** | Low | `evidence/judge_package/index.html` committed; FG mIoU 0.1989 (synthetic); SHA-256 manifest; `make judge` regenerates end-to-end. |
| **Evaluation Pipeline** | **Green** | Low | `run_calibrated_eval.py` produces provenance-rich JSON; baseline vs calibrated in one run; CI validates. |
| **Training Pipeline** | **Yellow** | Medium | `train.py` + `train_synthetic_demo.py` work; production training blocked by absent `data/`. Not required for submission if benchmark tarball ships. |
| **Documentation** | **Green** | Low | README judge quick start, `JUDGE_EXPERIENCE.md`, `official_metrics_for_submission.md` aligned. No contradictory headline metrics in active docs. |
| **API** | **Yellow** | Medium | FastAPI `/infer`, `/infer-tiff`, `/survey-report` implemented; requires checkpoints. Docker builds in CI. Untested live at submission scale without artifacts. |
| **Intelligence Layer** | **Green** | Low | `build_survey_intelligence`, explainability, spatial analysis; tests pass; integrated in judge package + API. |
| **Reproducibility** | **Green** | Low | `make judge`, `reproduce.sh`, GitHub Actions CI (pytest + reproduce). 35 tests, 64% coverage locally. |
| **Benchmark Framework** | **Yellow** | **High** | `package_production_release.sh`, `verify_production_benchmark.sh`, manifest template exist. **No hosted `SVAMITVA_ARTIFACTS_URL`.** Production mIoU not clone-verifiable. |

**Summary:** 5 Green, 4 Yellow, 0 Red. **No Red blockers** for synthetic submission path. **Yellow → Red escalation risk** if benchmark packaging slips past Day 2.

---

## Phase 4 — Experiment Tracks

### Track A — `release/stable` (default after Day 2 EOD)

| Allowed | Forbidden |
|---------|-----------|
| P0 bug fixes (crash, wrong metrics, broken `make judge`) | Architecture changes |
| Doc accuracy fixes | API breaking changes |
| Packaging / manifest / URL fixes | Data format changes |
| Judge HTML regeneration from scripts | Removing features |
| Dependency pin fixes (security only) | Refactoring |

### Track B — `experiment/*` (Days 1–2 only, merge-or-discard by Day 3 AM)

| Allowed | Forbidden |
|---------|-----------|
| Bias search re-run on production ckpts | Breaking APIs |
| Post-processing threshold tuning | Changing shapefile schema |
| Augmentation experiments (branch only) | Removing survey intelligence |
| Partial retrain (≤20 epochs smoke) | Modifying `platform_config.v1.json` splits |
| Production eval re-run after packaging | |

**Merge rule:** Track B changes merge to stable **only if** eval FG mIoU improves ≥0.02 **and** `make judge` + full pytest pass on first try.

---

## Phase 5 — Experiment ROI Analysis

| Experiment | Expected IoU Gain | Effort | Risk | Go/No-Go |
|------------|-------------------|--------|------|----------|
| **Production benchmark tarball + hosted URL** | **+0.00 IoU, +1.2–1.6 judge score** | 6–10 hr | Low | **GO** |
| Production panel in judge HTML | 0 (perception only) | 2–3 hr | Low | **GO** (Day 1–2) |
| Bias search re-run (existing ckpts) | +0.01–0.04 | 3–4 hr | Low | **GO** (Track B, Day 1) |
| Post-processing threshold tune | +0.01–0.03 | 2–4 hr | Medium | **GO** (Track B, Day 1) |
| Partial retrain (20 epochs) | +0.02–0.08 | 12–20 hr | **High** | **NO** (unless packaging done Day 1) |
| Full retrain (80 epochs) | +0.00–0.10 | 40–80 hr | **Critical** | **NO** |
| Architecture swap | +0.05–0.15 | 60+ hr | **Critical** | **NO** |
| Bridge class recovery | −0.1–0.05 | 20+ hr | **Critical** | **NO** |
| New Streamlit pages | 0 | 8+ hr | Low | **NO** |
| More documentation | 0 | 4+ hr | Low | **NO** |
| Synthetic training epochs (+20) | +0.02–0.05 synthetic only | 4 hr | Low | **NO** (judges weight production) |

---

## Phase 6 — Lock-In Strategy

| Milestone | Day | Gate |
|-----------|-----|------|
| Benchmark tarball hosted + production eval committed | **Day 2 EOD** | Hard gate |
| **Release candidate freeze** | **Day 3 12:00** | `RELEASE_FREEZE_CHECKLIST.md` all green |
| Validation window | Day 3 PM – Day 4 | Bug fixes only |
| Submission package | Day 5 | Tag + archive + defense rehearse |

**Earliest safe freeze: Day 3** — only if Days 1–2 complete benchmark packaging.  
**Latest acceptable freeze: Day 3 EOD** — Day 4 must be validation-only.

After freeze: **no feature development**. Only P0 bugs, doc corrections, packaging fixes.

---

## Day 1 — Must-Finish Tasks

**Theme: Locate assets, secure rights, package benchmark.**

| # | Task | Owner | Hours | Done when |
|---|------|-------|-------|-----------|
| 1.1 | Locate production `best_model.pth`, `latest_model.pth`, `optimal_bias.json` | ML | 1 | Files on disk, SHA-256 recorded |
| 1.2 | Confirm redistribution rights (organizer email / hackathon terms) | Lead | 2 | Written yes/no |
| 1.3 | Copy 1–2 validation villages to `data/` (NADALA, NAGUL per `platform_config.v1.json`) | ML | 2 | `DatasetValidator` passes |
| 1.4 | Run `bash scripts/package_production_release.sh` | ML | 1 | Tarball + `ARTIFACT_MANIFEST.json` |
| 1.5 | Upload tarball; set `SVAMITVA_ARTIFACTS_URL` in README | Release | 2 | URL live, curl succeeds |
| 1.6 | Run production eval: `fetch → run_calibrated_eval.py --require-bias` | ML | 1 | `calibrated_eval_results.json` with real mIoU |
| 1.7 | Track B (parallel, optional): bias search on production ckpts | ML | 3 | Keep only if mIoU +0.02 |
| 1.8 | End-of-day smoke: `make judge` + `pytest` | QA | 0.5 | All green |

**Day 1 exit criteria:** Production benchmark URL works OR explicit decision documented that redistribution is denied (fallback: emphasize synthetic + archived methodology only).

---

## Day 2 — Must-Finish Tasks

**Theme: Integrate production evidence into judge-facing artifacts.**

| # | Task | Owner | Hours | Done when |
|---|------|-------|-------|-----------|
| 2.1 | Regenerate judge package with production metrics panel | ML | 2 | HTML shows synthetic + production side-by-side |
| 2.2 | Commit production `outputs/calibrated_eval_results.json` (if policy allows) | Release | 0.5 | Provenance intact |
| 2.3 | Write `DEMO_SCRIPT.md` — 3-min + 5-min flows | Lead | 2 | Rehearsed once |
| 2.4 | Fresh-clone validation on clean machine / CI | QA | 2 | `make judge` passes from scratch |
| 2.5 | Demo dry-run: Streamlit + API with fetched artifacts | Demo | 2 | No crash on happy path |
| 2.6 | Track B cutoff: merge winning experiments or discard branches | ML | 1 | No open experiment PRs |
| 2.7 | Tag pre-freeze: `v1.0.0-rc1` | Release | 0.5 | Tag pushed |

**Day 2 exit criteria:** Judge can verify production mIoU via URL + one command. Demo works with fetched artifacts.

---

## Day 3 — Release Candidate Freeze

**Morning (before 12:00):**

| # | Task |
|---|------|
| 3.1 | Complete `RELEASE_FREEZE_CHECKLIST.md` — every command green |
| 3.2 | Tag `v1.0.0-rc2` (freeze candidate) |
| 3.3 | Branch `release/stable` — lock Track A rules |

**Afternoon:**

| # | Task |
|---|------|
| 3.4 | Full regression: pytest, reproduce, judge package, docker build |
| 3.5 | Fix **P0 only** from regression |
| 3.6 | No new features after 12:00 |

**Freeze declaration:** Email/Slack to team: *"RC frozen. Only P0 fixes until submission."*

---

## Day 4 — Validation Only

| # | Activity | Forbidden |
|---|----------|-----------|
| 4.1 | Second fresh-clone test (different OS if possible) | New features |
| 4.2 | Judge-package visual review (overlays, metrics labels) | Refactoring |
| 4.3 | `SUBMISSION_DEFENSE.md` rehearsal (3-min + 5-min) | Architecture changes |
| 4.4 | `verify_production_benchmark.sh` on fetched tarball | Experiment merges |
| 4.5 | P0 bug fixes only → `v1.0.0-rc3` if needed | |

---

## Day 5 — Submission Preparation

| # | Task | Time |
|---|------|------|
| 5.1 | Final tag `v1.0.0` | 09:00 |
| 5.2 | Submission archive: repo link + `SVAMITVA_ARTIFACTS_URL` + judge HTML path | 10:00 |
| 5.3 | One-page submission summary (problem → solution → metrics → verify command) | 11:00 |
| 5.4 | Presenter handoff: `DEMO_SCRIPT.md`, `SUBMISSION_DEFENSE.md`, printed metrics sheet | 12:00 |
| 5.5 | Submit | Before deadline |
| 5.6 | Post-submit: freeze branch, no further commits | — |

---

## Phase 9 — Final Recommendation

**If only one improvement can be pursued before freeze:**

### **B — Benchmark Packaging**

| Metric | Value |
|--------|-------|
| Expected judge score gain | **+1.2 to +1.6** composite (6.7 → 7.9–8.3) |
| Expected IoU gain | 0.00 new training; **enables verification of ~0.39** already achieved |
| Effort | 6–10 hours |
| Probability of success | **0.85** (if checkpoints exist locally) |
| Worst-case downside | 6 hours lost if redistribution denied; submission unchanged (still Strong Contender at ~6.7) |

**Why not A (Retraining):** 40–80 GPU-hours, may not beat existing epoch-43/80 ensemble, high regression risk, misses Day 3 freeze.

**Why not C/D/E:** Demo, docs, features already 8+/10; marginal +0.1 ceiling. Cannot close the 0.20 vs 0.39 mIoU perception gap.

**Commit: Benchmark packaging is the only remaining high-EV use of pre-freeze hours.**

---

*Companion documents: `RELEASE_FREEZE_CHECKLIST.md`, `SUBMISSION_DEFENSE.md`, `RISK_REGISTER.md`, `SCORE_MAXIMIZATION_PLAN.md`*
