# Metric Cleanup Inventory

Purpose: classify metric references discovered during repository sweep and mark cleanup actions.

Source-of-truth policy:
- Board-facing metrics must come only from `official_metrics_for_submission.md`.

## Current Metrics (Allowed)

| Category | File(s) | Status |
|---|---|---|
| Official board-facing metrics | `official_metrics_for_submission.md` | Active |
| Board summary with aligned official values | `executive_board_package.md`, `final_competition_narrative.md`, `judge_defense_book.md`, `README.md`, `submission_document.md`, `docs/SYSTEM_OVERVIEW.md`, `demo_ui/README.md` | Sanitized |
| Final calibrated metric artifact | `outputs/calibrated_eval_results.json` | Active canonical artifact |

## Retired Metrics (Removed From Submission-Facing Docs)

Retired examples removed from submission-facing files include:
- legacy pre-final mIoU claims
- legacy built-up and infrastructure summary claims
- legacy checkpoint epoch claims

Files sanitized for retired metric removal:
- `README.md`
- `submission_document.md`
- `docs/SYSTEM_OVERVIEW.md`
- `demo_ui/README.md`
- `official_metrics_for_submission.md` (retired numeric list removed)
- `audit_model.py` (legacy literal comparisons removed)

## Conflicting Metrics Found During Full Sweep

Conflicting values still exist in non-submission historical artifacts, including:
- training history and training logs under `outputs/`
- bridge experimental campaign artifacts under `outputs/bridge_campaign/` and `outputs/bridge_phase3/`
- historical recovery logs under `outputs/recovery_logs/`

Disposition:
- These are classified as engineering/experimental history, not board-facing submission claims.
- They are excluded from submission scoring references.

## Cleanup Outcome

- Submission-facing documents now reference one metric lineage.
- Every required updated file includes metric provenance.
- Judge-safe package generated for one-table submission use.