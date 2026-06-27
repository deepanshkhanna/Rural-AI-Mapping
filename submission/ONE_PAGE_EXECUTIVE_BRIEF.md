# One-Page Executive Brief

**SVAMITVA Geospatial Intelligence Platform** | v1.0-certified | Read time: 3 minutes

---

## Problem

SVAMITVA maps rural India using drone orthomosaics. Before property cards are issued, survey teams must manually digitize roads, settlements, and water bodies — a bottleneck of days to weeks per village. This delays land rights for millions of rural households.

## Approach

We automate infrastructure extraction from orthomosaics using a supervised deep learning pipeline with geospatial validation, calibrated inference, and human-in-the-loop survey intelligence. The system produces GIS-ready segmentation masks and structured field recommendations — not just model predictions.

## Architecture

| Component | Detail |
|-----------|--------|
| Model | DeepLabV3Plus + ResNet50 (27M parameters, 768 px input) |
| Training | 6 villages, village-held-out split, Focal Tversky loss |
| Inference | 2-checkpoint ensemble (65/35) + logit calibration + TTA + geospatial postprocessing |
| Classes | Road, Built-Up Area, Water Body (operational); Bridge (non-operational) |
| Output | GeoTIFF masks, per-class statistics, survey intelligence reports |

## Results

**Certified on 598 held-out patches from 2 validation villages (NADALA, NAGUL):**

| Metric | Value |
|--------|-------|
| **FG mIoU** | **0.4809** |
| Road IoU | 0.4356 (recall 0.64) |
| Built-Up IoU | 0.7415 |
| Water IoU | 0.7466 |

Per-village: NADALA FG 0.5882 | NAGUL FG 0.4124 (domain shift reported transparently).

All metrics reproducible: `run_calibrated_eval.py --require-bias`. SHA-256 checksums on all artifacts.

## Impact

- **Speed:** Minutes of GPU inference vs days of manual GIS digitization per village
- **Coverage:** Roads, settlements, and water — the three classes survey teams spend the most time mapping
- **Quality:** Human reviewers focus on flagged low-confidence zones, not tracing from scratch
- **Scale:** Stateless inference scales horizontally across GPU fleet for national processing
- **Sovereignty:** Fully offline — no cloud APIs, no data leaves government infrastructure

## Deployment Readiness

| Capability | Status |
|------------|--------|
| Docker API (FastAPI) | Ready |
| Offline operation | Ready |
| Security (API key, upload validation, safe checkpoint loading) | Ready |
| Full GeoTIFF tiling inference | Ready |
| Streamlit demo + HTML evidence bundle | Ready |
| Checksum-verified artifacts | Ready |
| Vector export (GeoPackage) | **Shipped** (building footprints, roads, water) |
| Roof_type codes 1–4 | **Experimental** (~36% coverage on demo tile) |
| State-level pilot | Roadmap (1 month) |

## Verify Independently

```bash
pip install -r requirements.txt && make judge
# Open evidence/judge_package/index.html
```

## Bottom Line

A frozen, auditable, deployable geospatial AI system that accelerates SVAMITVA map production — with honest metrics, rejected alternatives documented, and production infrastructure included. Not a model demo. A survey operations platform.

**Contact:** See `README.md` | **Lock file:** `submission/SUBMISSION_LOCK.md`
