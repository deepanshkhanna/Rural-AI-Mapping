# SVAMITVA Geospatial Intelligence Platform

**Village survey intelligence from drone orthomosaics** — geospatially correct segmentation plus road-access analysis, settlement fragmentation, explainability review zones, and written field recommendations.

End-to-end pipeline for SVAMITVA infrastructure intelligence. Operational classes: Road, Built-Up Area, Water Body. Bridge is non-operational and excluded from success claims.

**Open first:** `PROJECT_BIBLE.md` — demo playbook, claims, recovery. Then `evidence/judge_package/index.html`.

## Stable Release

Current certified release: **`v1.0-certified`**

This release is frozen. All future work occurs in experimental branches (`experiment/main`, `research/`).

Stable metrics:

| Metric | Value |
|--------|-------|
| FG mIoU | 0.4809 |
| Road IoU | 0.4356 |
| Water IoU | 0.7466 |
| Built-Up IoU | 0.7415 |
| Bridge IoU | 0.0000 |
| Confidence | 0.82 |

Documentation:

- [PROJECT_BIBLE.md](PROJECT_BIBLE.md) — **start here** (demo, claims, recovery)
- [MODEL_CARD.md](MODEL_CARD.md)
- [BENCHMARK_CARD.md](BENCHMARK_CARD.md)
- [DATASET_CARD.md](DATASET_CARD.md)
- [SVAMITVA_SUBMISSION_CERTIFICATION.md](SVAMITVA_SUBMISSION_CERTIFICATION.md)

Recovery: see `RECOVERY_BUNDLE_REPORT.md`, `CHECKPOINT_RECOVERY.md`, and `BASELINE_SNAPSHOT.md`.

## Judge Quick Start (one command)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
make judge
# Open evidence/judge_package/index.html
```

This trains a synthetic verification model, runs calibrated eval, and writes a self-contained HTML evidence bundle with SHA-256 manifest. See `JUDGE_EXPERIENCE.md`.

## Judge Evidence Package (open first)

```bash
make judge-package
# Open evidence/judge_package/index.html in a browser
```

Self-contained visual report: GT vs prediction, error maps, confidence, survey intelligence, SHA-256 verification manifest.

Streamlit: `streamlit run demo_ui/app.py` → **Judge Verification** page.

## Reproducibility

All metrics must be regenerated from code — never cited from markdown alone.

### CI / local verification (synthetic fixtures)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
bash scripts/reproduce.sh
```

This builds synthetic geodata + dummy checkpoints, runs `run_calibrated_eval.py`, and writes `outputs/calibrated_eval_results.json` with full provenance (git SHA, checkpoint hashes, bias vector).

### Production evaluation (real orthomosaics)

```bash
export SVAMITVA_ARTIFACTS_URL="<release-tarball-url>"
bash scripts/fetch_artifacts.sh
python run_calibrated_eval.py --require-bias
```

Requires `outputs/checkpoints/best_model.pth`, `latest_model.pth`, `outputs/optimal_bias.json`, and `data/` orthomosaics + shapefiles.

## Metric Provenance

| Item | Source |
|---|---|
| Evaluator | `run_calibrated_eval.py` → `compute_counts_metrics` |
| Baseline vs calibrated | Computed in one run (no hardcoded comparators) |
| Postprocessing | Raw biased logits passed to `postprocess_mask` (no double-softmax) |
| Results artifact | `outputs/calibrated_eval_results.json` |
| Historical board metrics | Archived in `docs/audit-archive/` — superseded by reproducible eval |

## Quick Start

```bash
pip install -e ".[dev]"
pytest
streamlit run demo_ui/app.py          # demo UI
uvicorn production.api:app --port 8000  # production API (requires checkpoints)
```

## Core Entry Points

| Script | Purpose |
|---|---|
| `train.py` | Training with dataset preflight validation |
| `run_calibrated_eval.py` | Official baseline + calibrated evaluation |
| `scripts/reproduce.sh` | End-to-end synthetic reproduce |
| `scripts/build_synthetic_fixtures.py` | Generate CI test fixtures |
| `production/api.py` | FastAPI service with sliding-window `/infer` |
| `demo_ui/app.py` | Streamlit demo |

## Architecture Highlights

- CRS reprojection + geometry repair in `UnifiedMultiClassDataset`
- `CalibratedEngine.predict_large` / `predict_tiff` for orthomosaic tiling with georeferenced output
- Secure checkpoint loading (`weights_only=True`)
- GitHub Actions CI (`.github/workflows/ci.yml`)

## Configuration

- Production: `config/platform_config.v1.json`
- Synthetic CI: `config/platform_config.synthetic.json` (set `SVAMITVA_CONFIG_PATH`)

## License

MIT — see `LICENSE`.
