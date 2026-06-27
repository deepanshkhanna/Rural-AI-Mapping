# Dead Code Audit

**Date:** 2026-06-27  
**Rule:** Delete only with zero imports and zero execution paths. When uncertain → ARCHIVE.

## Active Entry Points (KEEP)

| File | Evidence |
|------|----------|
| `train.py` | Training entry (protected) |
| `run_calibrated_eval.py` | Official eval (protected) |
| `bias_search.py` | Referenced by eval, judge Q&A, MANIFEST |
| `scripts/reproduce.sh` | `Makefile`, CI, docs |
| `scripts/judge_verify.sh` | `Makefile judge` |
| `scripts/generate_judge_package.py` | `make judge`, demo UI |
| `scripts/build_synthetic_fixtures.py` | pytest, CI, reproduce |
| `scripts/export_vectors.py` | `README.md` CLI path |
| `scripts/build_project_bible.py` | Refresh `PROJECT_BIBLE.md` metrics from `epoch_71_results.json` |
| `scripts/install_production_checkpoints.sh` | `README.md` |
| `scripts/fetch_artifacts.sh` | Reproduction docs |
| `scripts/package_production_release.sh` | Release packaging |
| `scripts/verify_production_benchmark.sh` | Benchmark verification |
| `production/api.py` | Docker / API service |
| `demo_ui/app.py` | Streamlit demo |
| `src/**` | Core library (protected) |

## Archived (was root clutter)

| File / Dir | Verdict | Evidence |
|------------|---------|----------|
| `audit_model.py` | **ARCHIVE** | Superseded; only self-references |
| `evaluate_model_statistics.py` | **ARCHIVE** | Legacy eval script |
| `test_inference.py` | **ARCHIVE** | Superseded by `run_calibrated_eval.py` |
| `visualize_training.py` | **ARCHIVE** | Training viz only |
| `experiments/` (bridge scripts) | **ARCHIVE** | No imports from active code |
| `tools/` (certification scripts) | **ARCHIVE** | One-off audits |
| `SUBMISSION_PACKAGE/` | **ARCHIVE** | Mirror of root + production_release |
| `scripts/demo_failure_probe.py` | **ARCHIVE** | Untracked debug probe |

## Historical (ARCHIVE — keep for audit trail)

| File | Verdict | Evidence |
|------|---------|----------|
| `scripts/production_certification_v2.py` | **ARCHIVE** | Epoch certification matrix; not in Makefile/CI |
| `archive/experiment/**` | **ARCHIVE** | Rejected experiments |
| `archive/research/**` | **ARCHIVE** | Forensics only |

## Missing / Not Restored

| File | Status |
|------|--------|
| `scripts/build_demo_dataset.py` | Not present on disk; demo tiles already built in `demo_dataset/` |
| `scripts/final_demo_rehearsal.py` | Not present |

## Orphan Check

All modules under `src/` are imported by `train.py`, `run_calibrated_eval.py`, `production/api.py`, `demo_ui/`, or tests.

## Rollback

See `submission/ROLLBACK_MANIFEST_2026-06-27.txt`.
