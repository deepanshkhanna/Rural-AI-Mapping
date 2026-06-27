# Judge First Impression

**Simulated:** First-time reviewer, 3-minute navigation test  
**Date:** 2026-06-27

## Can you find…?

| Item | ≤3 min? | Path | Notes |
|------|---------|------|-------|
| **Architecture** | ✅ Yes | `docs/ARCHITECTURE.md`, `submission/SUBMISSION_AUDIT.md` | Clear module boundaries |
| **Metrics** | ✅ Yes | `README.md` → `production_release/metrics/epoch_71_results.json` | FG mIoU 0.4809 prominent |
| **Demo** | ✅ Yes | `README.md` → `streamlit run demo_ui/app.py` | Install script documented |
| **Reproduction** | ✅ Yes | `make judge` / `scripts/reproduce.sh` | One-command path |
| **Outputs** | ✅ Yes | `production_release/`, `evidence/judge_package/index.html` | Self-contained HTML |

## 60-Second Path (works)

1. Open `README.md` — metrics + quick start visible immediately
2. `make judge` — builds verification bundle
3. Open `evidence/judge_package/index.html`

## Friction Points

| Issue | Severity | Mitigation |
|-------|----------|------------|
| Checkpoints require install script | Medium | Documented in README; `production_release/` ships copies |
| `docs/SYSTEM_OVERVIEW.md` shows stale metrics (0.3871) | **High** | Protected file — flagged; judges should use README + epoch_71 JSON |
| `docs/audit-archive/` clutter | Low | Historical; not linked from README |
| Submission docs restored from transcript backup | Medium | Verify checksums against `production_release/MANIFEST.json` |

## First Impression Score

**8 / 10** — Professional structure after cleanup; metrics and demo paths are obvious. Deduction for stale doc metrics and checkpoint install step.

## Recommended Judge Reading Order

1. `README.md`
2. `evidence/judge_package/index.html`
3. `submission/ONE_PAGE_EXECUTIVE_BRIEF.md`
4. `submission/SUBMISSION_LOCK.md`
5. `docs/ARCHITECTURE.md`
