# PROJECT BIBLE — SVAMITVA Geospatial Intelligence Platform

**Last updated:** 2026-06-27  
**Release:** `v1.0-certified` (frozen)  
**Purpose:** Single operational reference for demo, judges, and recovery. Open this before presenting.

Regenerate metrics block: `python scripts/build_project_bible.py`

---

## 1. Elevator pitch (30 seconds)

We automate **road, built-up, and water extraction** from SVAMITVA drone orthomosaics — geospatially correct masks, vector export, and survey intelligence. Certified **FG mIoU 0.4809** on held-out validation villages. **Experimental** second-stage roof classifier outputs official `Roof_type` integers 1–4 on building footprints.

---

## 2. Certified model (DO NOT RETRAIN FOR DEMO)

| Item | Value |
|------|-------|
| Winner | **epoch_71** ensemble (65% ep71 + 35% ep80 EMA) |
| FG mIoU | **0.4809** |
| Road IoU | 0.4356 |
| Built-Up IoU | 0.7415 |
| Water IoU | 0.7466 |
| Bridge IoU | 0.0 (non-operational — do not claim) |
| Val patches | 598 (NADALA + NAGUL) |
| Checkpoints | `outputs/checkpoints/best_model.pth` (ep71), `latest_model.pth` (ep80) |
| Bias | `outputs/optimal_bias.json` |
| Authoritative JSON | `production_release/metrics/epoch_71_results.json` |
| Lock file | `submission/SUBMISSION_LOCK.md` |

---

## 3. Demo day playbook (5 minutes)

### Start

```bash
cd /home/dk/ml_projects/iit_hackathon
bash scripts/start_demo_gpu.sh
# → http://localhost:8501
```

**GPU:** RTX 5070 / WSL2 needs PyTorch **2.7.1+cu128** and `LD_LIBRARY_PATH=/usr/lib/wsl/lib`. If GPU missing: `wsl --shutdown` from Windows, reopen WSL.

### Stop

```bash
pkill -f "streamlit run demo_ui"
pkill -f "uvicorn production.api"
```

### Live script

1. Select tile **`04_fattu_bhila_building_heavy`** (building-heavy, best for roof demo).
2. **TTA OFF** (~28s segmentation + ~22s vector/roof export on GPU).
3. Show **Segmentation Output** (Road red, Built-Up yellow, Water cyan).
4. Scroll to **Experimental Roof Classification** card (below green success bar).
5. Point to metrics: ~520 footprints, ~36% classified, codes 1–4 table.
6. **Download GIS Vectors (GeoPackage)** → open in QGIS → `building_footprints` → `roof_type_code`.

### Say

- "Frozen epoch_71 ensemble, FG mIoU 0.4809 on held-out villages."
- "GIS-ready GeoPackage: building footprints, roads, water bodies."
- "Experimental second stage: official SVAMITVA `Roof_type` integers 1–4 — same field as training shapefiles."

### Do NOT say

- RCC, Tin, Clay, Metal material names (no official codebook in repo).
- 95% accuracy or production-ready roof classification.
- Bridge detection works.
- Retrained or improved segmentation since certification.

---

## 4. System architecture

```
Orthomosaic GeoTIFF
    → CalibratedEngine.predict_tiff()     [segmentation — CERTIFIED]
        ensemble + bias + TTA + postprocess
    → Mask (Road / Bridge / Built-Up / Water / Background)
    → vector_export.mask_to_geopackage()  [vectors — SHIPPED]
        building_footprints, roads, water_bodies
    → RoofMaterialClassifier (ResNet18)   [EXPERIMENTAL]
        per-building crop → roof_type_code 1–4
    → Streamlit demo + GPKG download
```

| Layer | Status | Key files |
|-------|--------|-----------|
| Segmentation | **Certified / frozen** | `src/inference/calibrated_engine.py`, `demo_ui/inference_wrapper.py` |
| Postprocess | **Certified** | `src/postprocessing.py` |
| Vector export | **Shipped** | `src/export/vector_export.py`, `scripts/export_vectors.py` |
| Roof classifier | **Experimental** | `src/roof_material/`, `checkpoints/roof_material/best.pt` |
| Survey intelligence | **Shipped** | `src/intelligence/survey_report.py` |
| Production API | **Ready** (Starlette conflict in some envs) | `production/api.py` |
| Demo UI | **Primary judge surface** | `demo_ui/app.py` |

---

## 5. Demo dataset tiles

| Tile | Use case |
|------|----------|
| `04_fattu_bhila_building_heavy` | **Default demo** — buildings + roof classification |
| `03_timmowal_road_heavy` | Road network emphasis |
| `05_timmowal_mixed_infrastructure` | Roads + buildings + water |
| `06_nadala_validation_nadala` | Held-out validation village (stress test) |

Manifest: `demo_dataset/demo_manifest.json`  
All tiles: 8200×8200 px, EPSG:3857, ~105–153 MB each.

---

## 6. Roof classification (experimental)

### What it is

Second-stage **ResNet18** trained on official `Roof_type` field from `Built_Up_Area_typ.shp` (PB) and `Built_Up_Area_type.shp` (CG). Predicts integers **1, 2, 3, 4** — not text labels.

### Why codes, not "Tin" or "Clay"

Hackathon brief lists RCC/Tin as **examples**. Training shapefiles store **integers only**. No codebook mapping 1→material name ships with the hackathon data. Showing "Tin" would be invented — use codes and point to QGIS `roof_type_code`.

### Why coverage is ~36% on demo tile

| Cause | Detail |
|-------|--------|
| Small footprints | Mask → rooftop heuristic → polygonize creates many tiny fragments |
| Crop gate | `extract_polygon_crop()` skips polygons &lt; 32 px on a side |
| Result | ~186 / 520 buildings get a valid crop; rest stay `nan` |

This is a **pipeline limitation**, not low model confidence on classified buildings.

### Checkpoint

- Path: `checkpoints/roof_material/best.pt`
- Flag: `src/roof_material/flags.py` → `ROOF_CLASSIFIER_ENABLED=True`
- Val metrics (training run): macro-F1 ~69.4%, accuracy ~82.2%

---

## 7. Environment & GPU

| Component | Requirement |
|-----------|-------------|
| Python venv | `.venv/` |
| PyTorch | **2.7.1+cu128** (RTX 50-series / sm_120) |
| WSL GPU | `export LD_LIBRARY_PATH=/usr/lib/wsl/lib` |
| Streamlit | `scripts/start_demo_gpu.sh` |
| Inference device | `SVAMITVA_INFERENCE_DEVICE=cuda` (default in start script) |

Large ortho fast path: postprocess skips slow bridge recovery when `h*w > 25M` pixels (`calibrated_engine.py`).

---

## 8. Key commands

```bash
# Demo (frontend)
bash scripts/start_demo_gpu.sh

# Production API (backend) — optional, not required for Streamlit demo
uvicorn production.api:app --host 0.0.0.0 --port 8000

# Official eval (reproduce metrics)
python run_calibrated_eval.py --require-bias

# Vector export CLI
python scripts/export_vectors.py \
  --tiff demo_dataset/tiffs/04_fattu_bhila_building_heavy.tif \
  --output outputs/roof_test.gpkg --device cuda

# Judge evidence bundle
make judge-package

# Offline judge package (roof GPKG + preview)
python scripts/build_judge_package.py
```

---

## 9. Claim matrix

| Claim | Verdict |
|-------|---------|
| FG mIoU 0.4809 | ✅ Certified |
| Water / Built-Up / Road IoU | ✅ Certified |
| GeoTIFF + GPKG vector export | ✅ Shipped |
| Survey intelligence / field priorities | ✅ Shipped |
| Roof_type codes 1–4 on footprints | ⚠️ Experimental (~36% coverage on demo tile) |
| RCC / Tin / Clay material names | ❌ Not in training data — do not claim |
| 95% accuracy | ❌ Not verified |
| Bridge detection | ❌ IoU 0.0 |
| Production roof materials | ❌ Experimental only |

---

## 10. Known issues & workarounds

| Issue | Workaround |
|-------|------------|
| GPU not visible in WSL | `wsl --shutdown` from Windows, reopen |
| Inference stuck at "Finalizing mask" | Fixed: fast postprocess on large orthos; restart Streamlit |
| Roof panel not visible | Scroll below green bar; re-run inference after code update |
| FastAPI test failure | Starlette version conflict — demo via Streamlit only |
| `judge_package/` empty | Run `scripts/build_judge_package.py` after `outputs/roof_test.gpkg` exists |
| Multiple Streamlit instances | `pkill -f "streamlit run demo_ui"` then restart once |

---

## 11. File map (open these first)

| File | Why |
|------|-----|
| `PROJECT_BIBLE.md` | This document |
| `submission/SUBMISSION_LOCK.md` | Frozen config contract |
| `submission/JUDGE_QA_MASTER.md` | **55 judge Q&A** (roof codes, GPKG, demo) |
| `submission/DEMO_PRESENTATION_READY.md` | Short demo recovery card |
| `production_release/metrics/epoch_71_results.json` | Certified metrics |
| `demo_ui/app.py` | Streamlit demo + roof panel |
| `config/platform_config.v1.json` | Class taxonomy, splits |
| `evidence/judge_package/index.html` | Offline HTML evidence |

---

## 12. Recovery history (2026-06-27)

- Rollback lost demo UI roof wiring → restored from stash `53577645` + commit `282d8e57`.
- GPU: PyTorch cu128 + WSL GPU passthrough restored.
- Streamlit: progress callbacks, fast postprocess, roof panel cached in session state.
- Servers stopped on demand via `pkill` (frontend 8501, backend 8000).

---

## 13. Related docs

- `README.md` — install, reproduce, CI
- `submission/ONE_PAGE_EXECUTIVE_BRIEF.md` — executive summary
- `docs/demo_instructions.md` — extended demo notes
- `docs/SYSTEM_OVERVIEW.md` — architecture deep dive

**Bottom line:** Segmentation is certified and frozen. Demo sells **GIS automation + honest experimental roof codes**. Never invent material names or accuracy you cannot prove from `epoch_71_results.json`.
