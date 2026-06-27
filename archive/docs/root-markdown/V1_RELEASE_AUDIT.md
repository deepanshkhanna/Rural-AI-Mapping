# V1 RELEASE AUDIT

**Date:** 2026-06-16  
**Auditor:** Automated V1 preservation program  
**Verdict:** **PASS** (with noted working-tree items excluded from commit)

## 1. Working Tree

| Check | Status | Notes |
|-------|--------|-------|
| Core V1 artifacts present | PASS | `production_release/`, `SUBMISSION_PACKAGE/` |
| Certification docs present | PASS | All cards and certification reports |
| `.gitignore` restored | PASS | Restored from HEAD; updated for V1 freeze |
| Ephemeral caches excluded | PASS | `.venv/`, `__pycache__/`, `.coverage` in gitignore |
| Training campaign scripts removed | INFO | Legacy campaign scripts deleted (intentional cleanup) |

**Pre-commit state:** Working tree contained unstaged deletions and untracked V1 artifacts. Release commit stages certified artifacts only.

## 2. Production Release Integrity

| Artifact | Present | Manifest Match |
|----------|---------|----------------|
| `checkpoints/best_model.pth` | YES | YES |
| `checkpoints/latest_model.pth` | YES | YES |
| `bias/optimal_bias.json` | YES | YES |
| `metrics/epoch_33_results.json` | YES | YES |
| `metrics/epoch_69_results.json` | YES | YES |
| `metrics/epoch_71_results.json` | YES | YES |
| `metrics/epoch_80_results.json` | YES | YES |
| `MANIFEST.json` | YES | N/A |
| Certification reports (5) | YES | N/A |

**MANIFEST verification:** 7/7 checksums PASS.

## 3. Submission Package

| Check | Status |
|-------|--------|
| Self-contained eval pipeline | PASS |
| Frozen production_release copy | PASS |
| MODEL_CARD, BENCHMARK_CARD, DATASET_CARD | PASS |
| `run_calibrated_eval.py` + `bias_search.py` | PASS |

## 4. Partially Generated / Temporary Files

| Path | Action |
|------|--------|
| `outputs/guardian/*.pid` | Excluded (gitignored via `outputs/**`) |
| `logs/training.log` | Excluded |
| `downloads/` | Excluded |
| `recovery_bundle/` | Excluded (local assembly dir) |
| `recovery_bundle_v1.zip` | Excluded (GitHub release asset) |

## 5. Broken Links

Markdown link scan on key certification docs: **0 broken links**.

## 6. Missing Checkpoints / Manifests

None. All certified artifacts accounted for in `production_release/MANIFEST.json` and `BASELINE_SNAPSHOT.md`.

## 7. Reproducibility Status

Independent dry-run (see `RECOVERY_VERIFICATION_REPORT.md`):

- FG mIoU reproduced: **0.4809** (exact match)
- All per-class IoU values match certified epoch_71 results

## Summary

The repository is **certified submission-ready**. V1 freeze commit captures all immutable production assets, documentation, and isolation policy. Experimental work is directed to `research/` on `experiment/main`.
