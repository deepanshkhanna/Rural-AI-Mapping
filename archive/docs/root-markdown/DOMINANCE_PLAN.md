# DOMINANCE_PLAN.md

High-leverage improvements to move from **Competitive (7.2)** to **Strong Contender** in a geospatial AI hackathon judged by senior engineers.

---

## Phase 1 — Competitive Gap Analysis (Summary)

### What prevents "Exceptional"?

| Blocker | Why judges care |
|---|---|
| No judge-openable evidence bundle | Engineers distrust markdown metrics; they want visual + cryptographic proof |
| No "so what?" layer | Segmentation alone is commodity; Panchayati Raj needs survey intelligence |
| Production metrics external | Cannot verify headline IoU without release artifacts |
| Demo shows masks, not decisions | Missing decision-support narrative |

### Commodity vs uncommon

| Commodity | Uncommon in this repo (after dominance work) |
|---|---|
| DeepLabV3+ training | **Survey intelligence** (road access, fragmentation, recommendations) |
| Streamlit overlay | **Judge evidence HTML** with GT/pred/error maps + SHA-256 manifest |
| FastAPI infer | **`/survey-report`** decision-support API |
| TTA + postprocess | **Explainability report** with review zones |

---

## Phase 3 — Execution Filter

| Improvement | Effort | Risk | Judge Impact | Technical Impact | Approved |
|---|---|---|---|---|---|
| Judge evidence package (`generate_judge_package.py`) | Medium | Low | **High** | High | ✅ |
| Survey intelligence layer (`src/intelligence/`) | Medium | Low | **High** | High | ✅ |
| `/survey-report` API endpoint | Low | Low | **High** | Medium | ✅ |
| Demo decision-support + Judge Verification page | Low | Low | **High** | Medium | ✅ |
| Synthetic demo training for evidence | Medium | Medium | **High** | Medium | ✅ |
| Production artifact release URL | Low | Low | **High** | High | ⏳ (requires operator) |

Rejected (Judge Impact = Low): print→logger migration, audit archive moves, coverage 85% drive.

---

## Phase 4 — Hackathon Killer Features (Designed & Implemented)

### Explainability
- `build_explainability_report()` — per-class confidence, review zones, audit notes
- Confidence heatmaps in judge package and demo

### Spatial Intelligence
- `analyze_spatial_intelligence()` — road connectivity, built-up road access %, water proximity, fragmentation, recommendations

### Decision Support
- `build_survey_intelligence()` — executive summary + infrastructure stats + recommendations
- Demo downloadable JSON survey report
- API `/survey-report`

### Evidence Generation
- `evidence/judge_package/index.html` — self-contained visual report
- `verification_manifest.json` — SHA-256 per file
- `metrics.json` — GT vs prediction on synthetic ortho
- `survey_intelligence.json`

---

## Commands

```bash
make judge-package    # train + eval + evidence bundle
streamlit run demo_ui/app.py   # includes Survey Intelligence + Judge Verification page
```
