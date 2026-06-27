# Submission Defense Guide

**Audience:** Presenters and technical leads facing hackathon judges.  
**Tone:** Honest, evidence-first, no overclaiming.

---

## What Judges Will Like

1. **One-command verification** — `make judge` → HTML evidence pack with SHA-256 manifest.
2. **Geospatial engineering depth** — CRS reprojection, GSD from affine transform, sliding-window orthomosaic inference, georeferenced GeoTIFF output.
3. **Decision support beyond masks** — Survey intelligence: road access, fragmentation, water proximity, review zones, written recommendations.
4. **Provenance discipline** — Every metric traces to `outputs/calibrated_eval_results.json` or `evidence/judge_package/metrics.json`; git SHA and checkpoint hashes in JSON.
5. **Honest scope** — Bridge explicitly non-operational; no fabricated production numbers.
6. **Production-ready surface** — FastAPI with `/infer`, `/infer-tiff`, `/survey-report`; Docker; secure checkpoint loading.

---

## What Judges May Attack

| Attack | Severity |
|--------|----------|
| "FG mIoU is only 0.20 on your evidence pack" | **High** |
| "Can you prove 0.39 on real data?" | **High** |
| "Road and Water IoU are zero" | Medium |
| "Why is Bridge in the model if it doesn't work?" | Medium |
| "Where is the training data?" | Medium |
| "This is engineering, not research novelty" | Low |
| "Built-Up IoU was 0.16 in old docs" | Low (if archived metrics cited) |

---

## How To Defend Each Decision

### "Low synthetic mIoU"

**Defense:** The committed judge package uses a **1024×1024 verification benchmark** to prove the pipeline end-to-end. It is labeled synthetic, not a production claim. Production metrics require the benchmark tarball (see README URL).

**Show:** `JUDGE_EXPERIENCE.md` — synthetic vs production table.

### "Unverifiable production claims"

**Defense:** We ship a checksum-verified release bundle. Run:

```bash
export SVAMITVA_ARTIFACTS_URL="<url>"
bash scripts/fetch_artifacts.sh
bash scripts/verify_production_benchmark.sh
SVAMITVA_CONFIG_PATH=config/platform_config.v1.json python run_calibrated_eval.py --require-bias
```

**Show:** `benchmark/ARTIFACT_MANIFEST.json`, production panel in judge HTML.

### "Road / Water IoU zero on synthetic"

**Defense:** Thin road (701 px) and full water polygon on a 1M-pixel raster with 20-epoch demo training — class imbalance on a toy benchmark. Production eval on NADALA/NAGUL shows operational class performance (cite production JSON per class).

**Do not say:** "Our model can't detect roads."

### "Bridge class"

**Defense:** Bridge is in the taxonomy for SVAMITVA completeness but **excluded from success metrics**. IoU 0.0 is documented. Roadmap item, not a hidden failure.

**Show:** README operational classes line.

### "Not novel"

**Defense:** Innovation is **geospatial decision intelligence** — converting segmentation into village survey reports with confidence and review zones — not a new backbone. Fit for deployment, not a paper.

**Show:** `survey_intelligence.json` in judge package.

### "Old Built-Up 0.16"

**Defense:** Superseded metric from an earlier eval configuration. Retired in `docs/audit-archive/`. Current numbers only from reproducible pipeline.

---

## Evidence To Show

| Priority | Artifact | What it proves |
|----------|----------|----------------|
| 1 | `evidence/judge_package/index.html` | Visual GT/pred/overlay/confidence/error |
| 2 | `evidence/judge_package/verification_manifest.json` | Integrity / non-tampering |
| 3 | `outputs/calibrated_eval_results.json` | Pipeline metrics + provenance |
| 4 | `benchmark/ARTIFACT_MANIFEST.json` | Production artifact checksums |
| 5 | `survey_intelligence.json` | Decision-support output |
| 6 | Live: `streamlit run demo_ui/app.py` | Interactive inference |
| 7 | Live: `curl` to `/survey-report` | API deployability |

---

## Metrics To Emphasize

| Metric | Context | Source |
|--------|---------|--------|
| **Production FG mIoU** (~0.39) | Real validation orthomosaics | Production `calibrated_eval_results.json` |
| **Per-class IoU (Road, Built-Up, Water)** | Production eval | Same artifact |
| **Built-Up IoU on synthetic** (~0.80) | Pipeline verification | Judge `metrics.json` |
| **Eval reproducibility** | Git SHA + checkpoint SHA-256 | `provenance` block |
| **Survey intelligence outputs** | Access, fragmentation, recommendations | `survey_intelligence.json` |

Always pair a number with its **source file** and **synthetic vs production** label.

---

## Metrics Not To Overclaim

| Do NOT claim | Why |
|--------------|-----|
| FG mIoU 0.39 from clone-only | Requires benchmark fetch |
| Bridge operational | IoU 0.0 by design |
| Synthetic 0.20 as production performance | Misleading |
| Archived 0.3871 without fresh eval artifact | Retired unless regenerated |
| "State-of-the-art" / "best in class" | Unprovable |
| Water IoU from synthetic benchmark | Currently ~0.0 |

---

## Three-Minute Demo Flow

| Time | Action | Script |
|------|--------|--------|
| 0:00–0:20 | Problem | "SVAMITVA villages need automated infrastructure maps from drone orthomosaics." |
| 0:20–0:40 | Open judge HTML | `evidence/judge_package/index.html` — scroll provenance + overlays |
| 0:40–1:10 | Metrics | "Synthetic verifies the pipeline. Production FG mIoU X.XX — reproducible via one command." |
| 1:10–1:50 | Survey intelligence | Expand recommendations in HTML or Streamlit Survey Intelligence |
| 1:50–2:20 | Live inference | Streamlit: upload synthetic TIFF → show overlay |
| 2:20–2:50 | Verification | Terminal: `make judge` or `verify_production_benchmark.sh` |
| 2:50–3:00 | Close | "Segmentation + geospatial correctness + village decision support — verified, not claimed." |

---

## Five-Minute Deep-Dive Flow

| Time | Topic | Depth |
|------|-------|-------|
| 0:00–0:30 | Architecture slide / `docs/ARCHITECTURE.md` | Data → train → ensemble → bias → postprocess → API |
| 0:30–1:30 | Geospatial | CRS, shapefile rasterization, `predict_large` tiling |
| 1:30–2:30 | ML pipeline | Two-model EMA, bias calibration, TTA, class handling |
| 2:30–3:30 | Evidence + metrics | Judge HTML + production eval JSON walkthrough |
| 3:30–4:15 | Intelligence layer | `build_survey_intelligence` — access, fragmentation, review zones |
| 4:15–4:45 | API / deploy | `/survey-report`, Docker, security |
| 4:45–5:00 | Q&A buffer | Hand off to `official_metrics_for_submission.md` |

---

## Pre-Presentation Checklist

- [ ] `SVAMITVA_ARTIFACTS_URL` tested this morning
- [ ] Streamlit starts; sample file ready
- [ ] Judge HTML open in browser tab
- [ ] Production metrics printed from JSON (not memory)
- [ ] Bridge non-operational line rehearsed
- [ ] Laptop on power; GPU drivers checked if using CUDA demo
