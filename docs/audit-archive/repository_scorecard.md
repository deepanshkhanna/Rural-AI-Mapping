# Repository Scorecard

Date: 2026-06-07
Audit mode: Independent external red-team review

## Category Scores

- Security: 3.8/10
- Data Governance: 3.2/10
- GitHub Hygiene: 2.9/10
- Python Engineering: 5.1/10
- ML Engineering: 5.0/10
- DevOps: 3.4/10
- Documentation: 4.3/10
- Architecture: 5.4/10

Overall Repository Score: 4.1/10

Scoring method:
- Harsh weighting toward production/governance risk over research novelty.
- Any unauthenticated production surface, stale schema docs, and geodata leakage indicators heavily penalized.

## Phase 11 Production Readiness Verdict

Verdict: D. Research Project

Evidence basis:
- Security controls incomplete for exposed API surface (`production/api.py`).
- Data governance risk is high due raw geospatial artifact footprint and location-identifiable metadata.
- DevOps hardening incomplete (no CI workflows, no container baseline, non-pinned dependencies).
- Documentation has critical stale architecture/class taxonomy mismatch.

Why not C (Prototype):
- Prototype-level maturity usually still requires minimally coherent deployment hardening and clearer governance boundaries than observed.

Why not B/A (Pilot/Production Ready):
- Current security, governance, and operational controls are materially insufficient for procurement-grade or government-board approval.
