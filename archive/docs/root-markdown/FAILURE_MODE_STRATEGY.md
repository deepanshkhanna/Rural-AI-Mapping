# Failure Mode Strategy — No Production Benchmark

**Assumption:** Checkpoints and/or validation orthomosaics cannot be redistributed. Legal approval does not arrive before deadline.

**Objective:** Maximize expected hackathon score without verifiable production mIoU.

**Principle:** Reframe the submission from *ML benchmark* to *deployable survey intelligence system*. Lead with what judges can see in 3 minutes.

---

## Phase 1 — Recalculated Score Ceiling

### Removed capability

| Lost | Impact |
|------|--------|
| Clone-verifiable FG mIoU ~0.39 | AI performance dimension capped |
| Production eval artifact | Trust dimension capped |
| `fetch_artifacts.sh` happy path | Benchmark credibility narrative weakened |

### New score ceiling (realistic)

| Dimension | Was (with bundle) | Now (no bundle) | Max achievable now |
|-----------|-------------------|-----------------|---------------------|
| AI performance (22%) | 7.5 | **4.5** | **5.0** (honest synthetic only) |
| Trust (18%) | 9.0 | **6.0** | **7.0** (transparent limits) |
| Real-world impact (12%) | 8.5 | **7.0** | **8.5** (narrative + demo) |
| Innovation (10%) | 8.0 | **7.5** | **8.5** (intelligence layer) |
| Demo quality (10%) | 9.0 | **8.5** | **9.5** (survey-first redesign) |
| Geospatial (12%) | 8.5 | **8.0** | **8.5** |
| Reproducibility (8%) | 9.0 | **8.0** | **8.5** |
| Engineering (5%) | 8.5 | **8.5** | **9.0** |
| Presentation (3%) | 8.5 | **8.0** | **9.0** |

**Composite:** 7.9–8.3 (with bundle) → **6.7–7.3** (without bundle)  
**Hard ceiling without new metrics:** ~**7.3 / 10**

### Biggest remaining weaknesses

1. **Synthetic FG mIoU 0.20** visible in judge HTML — first impression is "weak ML"
2. **Road/Water IoU 0.0** on evidence pack — looks like partial system failure
3. **No real village name** in demo — "Synthetic Verification Village" reads as toy

### Biggest remaining opportunities

1. **Survey intelligence is unique and implemented** — most teams stop at masks
2. **Judge HTML + Streamlit already contain recommendations** — buried below metrics
3. **Honest transparency** — if framed correctly, builds trust vs teams with unverifiable claims
4. **API `/survey-report`** — deployability story competitors often lack

---

## Phase 2 — Judge Psychology

**Reality:** Judges skim. They will not read `src/`. They will open 1–2 artifacts and maybe watch a demo.

| Artifact | P(judge sees it) | Why |
|----------|------------------|-----|
| **Judge Package (HTML)** | **90%** | README says "open first"; self-contained; no install |
| **README** | **75%** | Entry point; scanned for metrics and quick start |
| **Demo (Streamlit)** | **55%** | Live presentation or linked recording; requires run |
| **Survey Report JSON** | **40%** | Inside HTML or demo; rarely opened as raw file |
| **Metrics table in HTML** | **85%** | Prominent in judge pack — **works against us** today |
| **Architecture diagram** | **15%** | Only if in README or HTML; not standalone |
| **Source code** | **10%** | Spot-check only |
| **Tests / CI** | **20%** | Badge or README mention; rarely run |
| **API** | **25%** | Only if demo includes curl or live call |

**Implication:** Reorder judge HTML to show **Survey Intelligence before mIoU table**. Metrics section moves down with explicit "pipeline verification only" label.

---

## Phase 3 — Maximum Impact Without New Metrics

| Improvement | Est. score gain | Confidence | Mechanism |
|-------------|-----------------|------------|-----------|
| **Reorder judge HTML: intelligence first, metrics last** | +0.25–0.40 | High | Changes first impression in 90% viewed artifact |
| **3-min demo script: survey report, not mIoU** | +0.20–0.35 | High | Shifts impact + innovation dimensions |
| **Pre-recorded demo video (survey flow)** | +0.15–0.25 | Medium | Judges who skip install still see value |
| **Submission one-pager (government outcomes)** | +0.10–0.20 | High | README link; 60-second context |
| **Rename demo village + polish executive summary** | +0.05–0.15 | Medium | Reduces "toy" perception |
| **Methodology honesty box in HTML** | +0.10–0.15 | High | Trust without production bundle |
| **curl example for `/survey-report`** | +0.05–0.10 | Medium | Deployability signal |
| More synthetic training | +0.02–0.05 | Low | Judges weight production; marginal |
| New features / architecture | −0.10–0.05 | Low | Regression risk; reject |
| Claim archived 0.39 mIoU | **−0.30–0.50** | High | **Never do this** |

**Highest ROI:** Presentation reorder + demo narrative. Zero ML risk.

---

## Phase 4 — Competitor Counterstrategy

**Competitor profile:** Better mIoU, bigger model, more training data.

### Scenario A — Judge is a GIS engineer

They ask: *"Can I deploy this on a village orthomosaic and get a georeferenced report?"*

**Win:** Show `predict_tiff`, CRS handling, `/survey-report` JSON with GSD-aware metrics. Competitor with notebook mIoU may lack tiling API and decision-support layer.

### Scenario B — Judge is a survey / government stakeholder

They ask: *"What does my field team do with the output?"*

**Win:** Open `survey_intelligence.json` recommendations — road access %, review zones, written briefing. Competitor shows a confusion matrix; you show **"Field verification recommended for remote settlements."**

### Scenario C — Judge compares metrics tables first

They see competitor 0.42 mIoU vs your 0.20 synthetic.

**Mitigate:** Do not compete on that axis. Redirect in README and HTML: *"Metrics below verify pipeline integrity on synthetic benchmark. Submission value is survey intelligence — see Executive Summary."* Presenter must not apologize — pivot immediately to recommendations.

### Scenario D — Judge is skeptical of unverifiable claims

They ask: *"How do I know your numbers are real?"*

**Win:** `make judge` + SHA-256 manifest + honest synthetic labeling. Competitor with hand-typed README metrics loses trust. You lose on mIoU but win on **process integrity**.

---

## Phase 6 — Single Demonstration That Maximizes Score

**If judges watch only one thing:**

> **Streamlit inference → Survey Intelligence Report expander → read recommendations aloud.**

Or equivalent in judge HTML: **Executive Summary + recommendations** card at top.

### Redesign around this

| Artifact | Change |
|----------|--------|
| `generate_judge_package.py` HTML | Move Executive Summary + recommendations **above** metrics table; add "Pipeline Verification (Synthetic)" subheading on metrics |
| `demo_ui/app.py` | Survey Intelligence expander already `expanded=True` — add 1-line outcome headline above metrics sidebar |
| README | First bullet: "Produces village survey intelligence reports" not "FG mIoU" |
| Submission PDF/slide | Screenshot of recommendations list, not IoU table |
| `SUBMISSION_DEFENSE.md` | Open with survey report, not metrics |

---

## Phase 7 — Government Value (Evidence-Based)

| Stakeholder | Can help today? | Evidence |
|-------------|-----------------|----------|
| **Panchayats** | **Partially** | Recommendations flag settlements without road access and dispersed built-up clusters — inputs to village development planning |
| **Survey teams** | **Yes** | Review zones with centroids + confidence % direct **where to send field officers** (`explainability.review_zones`) |
| **State GIS departments** | **Yes** | CRS-correct pipeline, GeoTIFF I/O, FastAPI with georeferenced output — integrates with existing GIS stacks |
| **Rural planning officers** | **Partially** | Water proximity % and fragmentation index support setback and connectivity planning — requires reasonable segmentation input |

**Cannot claim today:** Cadastral-grade accuracy on real villages without production data in submission.

**Can claim today:** The **workflow from orthomosaic → intelligence report → field review prioritization** is implemented end-to-end on synthetic benchmark and ready for deployment when authorized data is available.

---

## Phase 8 — Remaining Days: Top 10 Actions

Ranked by expected score gain × confidence. **No benchmark packaging.**

| Rank | Action | Hours | Score gain | Confidence |
|------|--------|-------|------------|------------|
| 1 | Reorder judge HTML: intelligence first, metrics labeled synthetic | 2 | +0.30 | 0.90 |
| 2 | Write + rehearse 3-min survey-intelligence demo (`DEMO_SCRIPT.md`) | 3 | +0.25 | 0.85 |
| 3 | README rewrite: lead with survey intelligence, not mIoU | 1 | +0.15 | 0.90 |
| 4 | Record 3-min screen capture (Streamlit survey flow) | 2 | +0.20 | 0.75 |
| 5 | Submission one-pager (`WINNING_NARRATIVE.md` → PDF) | 2 | +0.15 | 0.80 |
| 6 | Add methodology honesty section to judge HTML | 1 | +0.12 | 0.85 |
| 7 | Screenshot pack: recommendations, review zones, overlay | 2 | +0.10 | 0.80 |
| 8 | README curl example for `/survey-report` | 0.5 | +0.08 | 0.70 |
| 9 | Freeze + validation per `RELEASE_FREEZE_CHECKLIST.md` | 4 | +0.05 | 0.95 |
| 10 | Presenter briefing: never cite archived 0.39; pivot to intelligence | 1 | +0.10 | 0.90 |

**Reject:** retraining, new architecture, bridge recovery, more audit docs, claiming production mIoU.

**Total effort:** ~18 hours  
**Expected composite gain:** +0.4 to +0.6 (6.7 → **7.1–7.3**)

---

## Final Answers

### Top quartile without production benchmark?

**NO**

**Evidence:**
- AI performance dimension remains **4.5/10** on 22% weight — largest single drag
- Competitors with verified 0.35–0.45 mIoU win the default judge comparison
- Narrative optimization ceiling ~7.3 vs top-quartile threshold ~7.8–8.0
- Strong Contender in **system completeness**; not top quartile in **ML leaderboard judging**

### Single strongest differentiator remaining

**The survey intelligence layer — `build_survey_intelligence()` converting segmentation masks into road-access analysis, settlement fragmentation metrics, explainability review zones, and written field recommendations via Streamlit and `/survey-report`.**

---

*Companion: `WINNING_NARRATIVE.md`, `SUBMISSION_DEFENSE.md`, `RELEASE_PLAN.md`*
