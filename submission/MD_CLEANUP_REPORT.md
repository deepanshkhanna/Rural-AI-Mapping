# Markdown Cleanup Report

**Date:** 2026-06-27

## Target

Root directory: **`README.md` only** (achieved).

## Actions

| Category | Count | Destination |
|----------|-------|---------------|
| Root markdown archived | 55 | `archive/docs/root-markdown/` |
| Root docx archived | 1 | `archive/docs/root-markdown/` |
| Submission planning docs archived | 0–9 | `archive/docs/planning/` (if present at cleanup time) |
| Judge-critical submission docs | 12 | Retained in `submission/` |

## Classification

### Submission-critical (kept in `submission/`)

- `SUBMISSION_LOCK.md`, `SUBMISSION_AUDIT.md`
- `COMPETITION_READINESS_REPORT.md`, `FINAL_SUBMISSION_REVIEW.md`
- `JUDGE_QA_MASTER.md`, `JUDGE_OBJECTIONS.md`, `HOSTILE_REVIEW.md`
- `DEMO_SCRIPT.md`, `PRESENTATION_AUDIT.md`, `ONE_PAGE_EXECUTIVE_BRIEF.md`
- `COMPETITIVE_POSITIONING.md`, `IF_WE_HAD_3_MONTHS.md`

### Reviewer-useful (kept in `docs/` — not modified)

- `docs/ARCHITECTURE.md`, `docs/EVALUATION.md`, `docs/TRAINING.md`, etc.

### Historical (archived)

- Plans, dominance reports, release audits, win analysis, score maximization, recovery reports → `archive/docs/root-markdown/`
- Internal sprint planning → `archive/docs/planning/`

### Forensics (already under `archive/research/forensics/`)

- Road/NAGUL/E06 forensics — unchanged

## Not Moved (protected)

- `docs/` content (per safety rules)
- `README.md`
- `production_release/reports/`

## Note

`docs/audit-archive/` (45 files) remains under `docs/` — candidate for future move to `archive/docs/audit-archive/` in a follow-up pass.

## Rollback

`submission/ROLLBACK_MANIFEST_2026-06-27.txt`
