# SUBMISSION PACKAGE REPORT

**Assembled:** 2026-06-16

## Location

`SUBMISSION_PACKAGE/`

## Contents policy

Included only reviewer-essential artifacts:

| Item | Included |
|------|----------|
| README (submission) | YES |
| MODEL_CARD | YES |
| DATASET_CARD | YES |
| BENCHMARK_CARD | YES |
| SVAMITVA_FINAL_PRODUCTION_DECISION | YES |
| FINAL_MODEL_CERTIFICATION | YES |
| production_release/ (checkpoints, bias, metrics, manifest, reports) | YES |
| Eval scripts + minimal `src/` | YES |
| Development history / POST_TRAIN_* | NO |
| docs/audit-archive | NO |
| Training logs | NO |

## Stats

- Total package size: **~715 MB** (checkpoints dominate)
- Checkpoints: `production_release/checkpoints/best_model.pth` + `latest_model.pth`
- Metrics: 4 candidate JSON files + certified epoch_71 stress results

## Integrity

`production_release/MANIFEST.json` SHA-256 checksums verified in `RELEASE_INTEGRITY_AUDIT.md`.

## Reviewer entry point

Open `SUBMISSION_PACKAGE/README.md` first.
