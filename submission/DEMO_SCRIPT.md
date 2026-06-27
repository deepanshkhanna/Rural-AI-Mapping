# Demo Script

**Total time:** 7 minutes (matches presentation slot)  
**Primary screen:** `evidence/judge_package/index.html` (pre-loaded)  
**Backup:** Streamlit `demo_ui/app.py` or screen recording

---

## Minute 0–1: Problem

### Talking Points

- "SVAMITVA is mapping rural India from the sky — drone orthomosaics at 0.3 metre resolution."
- "Before a household gets a property card, survey teams must digitize roads, settlements, and water bodies from these images."
- "That manual step is the bottleneck — weeks of GIS work per village."
- "We automate that extraction with a geospatially correct AI pipeline."

### Screen

- Slide 1: SVAMITVA orthomosaic example (aerial village image)
- Optional: split screen — manual GIS tracing vs our output mask

### Backup Explanation

If no slide image: "Imagine a high-resolution aerial photo of a village. Surveyors currently trace every road and building by hand in QGIS. We produce those layers automatically."

---

## Minute 1–2: Dataset

### Talking Points

- "We train on 6 village orthomosaics with official SVAMITVA shapefile labels."
- "We validate on 2 entirely held-out villages — NADALA and NAGUL — 598 patches, no leakage."
- "Every label is CRS-validated — EPSG 32643/32644 — geospatial correctness is not optional."
- "We report per-village results: NADALA FG 0.59, NAGUL FG 0.41 — we show hard cases."

### Screen

- Slide 3: Train/val village map or table from `config/platform_config.v1.json`
- Show village names on slide (credibility with GIS judges)

### Backup Explanation

"We split by village, not by patch. Patches from the same village never appear in both train and val. This is the correct methodology for spatial data — random patch splits would inflate metrics."

---

## Minute 2–4: Architecture

### Talking Points

- "DeepLabV3Plus with ResNet50 — 27 million parameters, 768-pixel input."
- "At inference: we ensemble epoch 71 (best validation) with epoch 80 EMA weights — 65/35 blend."
- "Per-class logit calibration tunes precision and recall without retraining."
- "Test-time augmentation — horizontal and vertical flip averaging."
- "Geospatial postprocessing: road gap fill connects fragments; bridge recovery uses spatial context."
- "We tested SegFormer — it scored 0.40 FG mIoU vs our 0.48. We kept what works."

### Screen

- Slide 4–5: Architecture diagram + pipeline flowchart
- **Live (if time):** Open `docs/ARCHITECTURE.md` pipeline section or HTML evidence pipeline tab

### Backup Explanation

"Think of it as four layers: the neural network produces class probabilities, calibration adjusts the decision boundaries, TTA reduces variance, and postprocessing fixes geospatial connectivity. Each layer is measured and frozen."

---

## Minute 4–5: Results

### Talking Points

- "Certified FG mIoU: **0.4809** on 598 held-out patches."
- "Road 0.44, Built-Up 0.74, Water 0.75."
- "Road is hardest — 1–2 pixel wide features — but recall is 0.64, we find most roads."
- "Bridge is non-operational — insufficient training pixels. We do not claim it."
- "Every number is reproducible: `run_calibrated_eval.py --require-bias`."

### Screen

- Slide 6: Results table (exact values from epoch_71_results.json)
- **Switch to:** `evidence/judge_package/index.html` — show GT vs prediction side by side

### Backup Explanation

"If the HTML does not load: all metrics are in `production_release/metrics/epoch_71_results.json` with SHA-256 checksums. Judges can verify independently with one command — `make judge`."

---

## Minute 5–6: Deployment

### Talking Points

- "This is not a notebook — it is a deployable system."
- "FastAPI service with Docker — `docker compose up`."
- "Fully offline — no cloud APIs, no data leaves the server."
- "API key authentication, upload validation, safe checkpoint loading."
- "Sliding-window tiling processes full village orthomosaics of any size."

### Screen

- Slide 9: Docker / API architecture
- **Live (if prepared):** `curl` to API health endpoint or Streamlit Judge Verification page

### Backup Explanation

"Deployment is standard government IT: Docker container on a GPU server, orthomosaics from NAS, masks to GIS team. No custom infrastructure. Recovery bundle is 1.3 GB with all checkpoints."

---

## Minute 6–7: Impact

### Talking Points

- "Beyond masks: road connectivity analysis, settlement fragmentation, and field review recommendations."
- "Survey teams verify flagged zones — humans stay in the loop."
- "Minutes of GPU time vs days of manual digitization per village."
- "Frozen, versioned, auditable — v1.0-certified with checksums."
- "This accelerates SVAMITVA's mission: accurate maps, faster property cards, empowered panchayats."

### Screen

- Slide 8 + 10: Survey intelligence screenshot + impact statement
- End on results number: **0.4809**

### Backup Explanation

"We are not claiming this replaces surveyors. We claim it makes them 10× more efficient by giving them a draft map and telling them exactly where to look."

---

## Demo Failure Playbook

| Failure | Action |
|---------|--------|
| No internet | Use pre-downloaded `evidence/judge_package/index.html` (self-contained) |
| GPU unavailable | Show HTML evidence (synthetic path); explain production needs GPU |
| Streamlit crash | Switch to HTML evidence or pre-recorded video (30 sec) |
| Judge asks live repro | "We can run `make judge` after this session — takes 2 minutes" |
| Judge challenges metric | Open `production_release/metrics/epoch_71_results.json` on screen |

---

## Post-Demo Handoff (Q&A)

Have these open in browser tabs:

1. `submission/JUDGE_QA_MASTER.md`
2. `production_release/metrics/epoch_71_results.json`
3. `evidence/judge_package/index.html`

**Assign roles:** One person answers GIS questions, one ML, one deployment.
