# Verified Repository Scorecard

Date: 2026-06-07
Method: Evidence-only recalculation from executed checks in this verification run

## Category Scores

| Category | Verified Score (/10) | Evidence Basis |
|---|---:|---|
| Security | 8.8 | Auth enforcement verified (401/200), upload restriction verified (400/200), strict checkpoint behavior verified, security tests passed |
| Data Governance | 8.0 | Raw data/checkpoint artifacts removed from baseline, placeholders present, acquisition policy documented; minor caveat: verification coverage artifact under `outputs/` |
| GitHub Hygiene | 6.2 | Ignore policy and placeholders valid, but orphan markdown set remains large (`ORPHAN_COUNT=31`) |
| Python Engineering | 8.3 | Entire test suite passes (18/18), compile/import health and pip check pass |
| ML Engineering | 6.4 | Model builds and training entrypoint works, but dataset and checkpoint absence blocks runtime training/eval execution |
| DevOps | 5.0 | Dockerfile/compose artifacts exist and compose YAML parses, but Docker runtime unavailable so build/run not verified |
| Documentation | 6.0 | No broken local markdown links, but many orphan docs reduce maintainability and traceability |
| Architecture | 7.6 | Production API boundary and inference imports load cleanly; architecture docs updated; full runtime integration limited by missing artifacts |

## Overall Verified Score

- **7.0 / 10** (simple average of the eight verified categories)

## Evidence Summary

- Full tests: `18 passed, 0 failed, 0 skipped`
- Broken markdown links: `0`
- Orphan markdown docs: `31`
- Training dry-run: starts and loads config, blocked at dataset availability
- Inference eval script: blocked at missing checkpoints
- Demo server: starts; full prediction path blocked by missing checkpoints
- Container runtime: not available in current environment

## Verified Conclusion

Projected remediation score (8.7/10) is **not fully verified** in this environment.
The evidence-backed verified score is **7.0/10**.
