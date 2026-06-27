# If We Had 3 Months

Judges frequently ask: "What would you do with more time?" Answer with specificity and honesty — show you think beyond the hackathon.

---

## If We Had 1 Week

**Goal:** Production pilot readiness and presentation polish.

| Priority | Action | Expected Outcome |
|----------|--------|------------------|
| 1 | Run production eval on all available test villages | Expand per-village stress table beyond NADALA/NAGUL |
| 2 | Add raster-to-vector export (GeoTIFF mask → shapefile) | GIS teams can import directly to QGIS/ArcGIS |
| 3 | Record 3-minute backup demo video | Demo failure insurance |
| 4 | Pilot timed comparison: manual digitization vs our pipeline on one village | Quantify surveyor-hour savings with real number |
| 5 | Polish judge HTML evidence with one real-village example | Stronger visual impact than synthetic |

**What we would NOT do:** Retrain or change model weights. v1.0 is frozen.

---

## If We Had 1 Month

**Goal:** Road improvement and deployment hardening.

| Priority | Action | Expected Outcome |
|----------|--------|------------------|
| 1 | **Road-focused iteration:** centerline loss + hard-negative mining on bare soil (exp06/exp07 learnings) | Target Road IoU 0.45+ without losing FG mIoU |
| 2 | **Active learning loop:** deploy on 3 new villages, collect human corrections, retrain | Data expansion with quality control |
| 3 | **DSM/elevation fusion** (exp01): add elevation channel where available | Better road/path disambiguation |
| 4 | **MLOps pipeline:** automated certification matrix on retrain | Any new model must beat 0.4809 to promote |
| 5 | **State pilot:** deploy Docker API in one survey department | Real-world feedback loop |
| 6 | **Monitoring dashboard:** inference latency, confidence distribution, error rate per village | Government operations visibility |

**Certification gate:** New model must beat FG mIoU 0.4809 on same 598-patch protocol to replace v1.0.

---

## If We Had 3 Months

**Goal:** Generalization and national-scale readiness.

| Phase | Weeks | Actions |
|-------|-------|---------|
| **Data** | 1–4 | Acquire 20+ villages stratified by terrain (plain, hilly, coastal, tribal); maintain village-level splits; include 5+ NAGUL-like hard villages |
| **Model** | 3–8 | Retrain with expanded data; test SegFormer and DeepLab with 20+ villages (transformers may win with scale); DSM multimodal for villages with elevation |
| **Road** | 5–10 | Topology-aware loss; OSM pre-training where available; road-centric multi-scale training (512 + 768 + 1024) |
| **Bridge** | 6–10 | Synthetic bridge augmentation; dedicated bridge sampler; only claim Bridge if IoU > 0.3 on val |
| **Eval** | 8–10 | Expand held-out set to 5+ villages; cross-state validation; full-raster eval alongside patch eval |
| **Deploy** | 9–12 | NIC integration pilot; batch processing pipeline for state-level orthomosaic archives; vector export + topology QA |
| **Certify** | 12 | Full certification matrix; promote to v2.0 only if FG mIoU > 0.52 on expanded held-out set |

**Realistic 3-month target:** FG mIoU 0.52–0.55 with 20+ training villages and improved Road IoU 0.48+.

---

## If We Had 1 Year

**Goal:** National SVAMITVA integration.

| Quarter | Focus |
|---------|-------|
| **Q1** | State-level pilots (3 states); measure surveyor-hour savings; expand training to 50+ villages |
| **Q2** | v2.0 model with multimodal input; Bridge class operational; national held-out benchmark (10+ villages) |
| **Q3** | Integration with SVAMITVA property card workflow; automated map sheet generation; field team mobile app for verification |
| **Q4** | Scale to 100+ villages training data; continuous learning pipeline; FG mIoU target 0.55+; formal security audit; NIC production deployment |

**1-year vision:** Every new SVAMITVA orthomosaic is auto-processed within 24 hours of upload, with human review limited to flagged zones.

---

## What We Would NOT Do (Even With Unlimited Time)

| Temptation | Why Not |
|------------|---------|
| Chase Bridge IoU without more bridge pixels | Cannot learn what is not in the data |
| Switch to SAM/GPT without measured gain | Architecture swaps must beat 0.4809 on same protocol |
| Train on val villages | Destroys generalization credibility |
| Report training loss as metric | Only held-out calibrated eval counts |
| Deploy without human-in-the-loop | Government requirement, not optional |

---

## How to Answer in 30 Seconds

> "One week: pilot metrics and vector export. One month: road improvement and state pilot. Three months: 20+ villages, multimodal elevation, target FG 0.52. One year: national SVAMITVA integration with continuous learning. Every step requires beating our certified 0.4809 on the same evaluation protocol — we do not ship regressions."
