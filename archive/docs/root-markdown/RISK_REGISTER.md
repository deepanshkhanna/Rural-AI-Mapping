# Risk Register — 5-Day Submission Sprint

**Last updated:** 2026-06-15  
**Review cadence:** Daily standup (Days 1–3), twice daily (Days 4–5)

---

## 1. Critical Risks

| ID | Risk | Likelihood | Impact | Mitigation | Owner |
|----|------|------------|--------|------------|-------|
| C1 | **Production checkpoints lost or inaccessible** | Medium (35%) | **Critical** — cannot ship benchmark; score capped ~6.7 | Day 1 priority: search all team storage, laptops, cloud buckets. Escalate to advisor immediately if missing. | ML Lead |
| C2 | **Redistribution of orthomosaics/checkpoints denied** | Medium (30%) | **Critical** — benchmark packaging blocked | Request expedited organizer approval Day 1 AM. Fallback: private judge-only link + manifest checksums. | Release Mgr |
| C3 | **Late retrain experiment breaks stable branch** | Medium (40%) if allowed | **Critical** — misses freeze, unstable submission | Track B only Days 1–2; merge gate: mIoU +0.02 AND full test pass. Hard cutoff Day 2 EOD. | Tech Lead |
| C4 | **Judge package regresses to 0.0 IoU** (bias bug recurrence) | Low (15%) | **Critical** — destroys credibility | `optimal_bias.json` synthetic zeros enforced in `build_synthetic_fixtures.py`; `make judge` in freeze checklist. | ML |

---

## 2. High Risks

| ID | Risk | Likelihood | Impact | Mitigation | Owner |
|----|------|------------|--------|------------|-------|
| H1 | **Tarball too large for judges to download** | Medium (35%) | High | Ship validation subset only (2 villages) + checkpoints; document size in README. | Release |
| H2 | **`SVAMITVA_ARTIFACTS_URL` broken at submission** | Medium (25%) | High | Test URL from external network Day 4; backup mirror; checksum in README. | Release |
| H3 | **Demo crashes live (missing checkpoints)** | Medium (30%) | High | Pre-fetch artifacts before presentation; synthetic fallback sample in `demo_ui/assets/`. | Demo |
| H4 | **Fresh clone `make judge` fails** | Low (20%) | High | Day 2 + Day 4 clean-machine test per freeze checklist. | QA |
| H5 | **Presenter cites archived 0.3871 without live eval** | Medium (35%) | High | Print metrics from current JSON only; rehearse `SUBMISSION_DEFENSE.md`. | Lead |
| H6 | **Freeze missed (Day 4 still merging features)** | Medium (30%) | High | Hard Day 3 12:00 freeze; Tech Lead enforces Track A rules. | Tech Lead |

---

## 3. Medium Risks

| ID | Risk | Likelihood | Impact | Mitigation | Owner |
|----|------|------------|--------|------------|-------|
| M1 | CI fails on submission day | Low (20%) | Medium | Verify CI green at freeze; no dependency bumps post-freeze. | DevOps |
| M2 | Docker build fails | Low (15%) | Medium | CI docker job; fix Day 1–2 only. | DevOps |
| M3 | API untested with production ortho size | Medium (40%) | Medium | Day 2 spot-test `/infer-tiff` on one validation village. | ML |
| M4 | Water/Road zero IoU visible in judge HTML | High (70%) | Medium | Label as synthetic; lead with production panel; defense script ready. | Demo |
| M5 | Competitor shows higher mIoU | High (80%) | Medium | Emphasize survey intelligence + geospatial + verification discipline. | Lead |
| M6 | GPU unavailable on demo machine | Medium (30%) | Medium | CPU fallback works; pre-run inference for backup screenshots. | Demo |

---

## 4. Low Risks

| ID | Risk | Likelihood | Impact | Mitigation | Owner |
|----|------|------------|--------|------------|-------|
| L1 | Streamlit port conflict | Low (15%) | Low | `--server.port 8502` documented. | Demo |
| L2 | Test coverage drops below 40% | Low (10%) | Low | No ML core changes post-freeze. | QA |
| L3 | Typo in README URL | Medium (25%) | Low | Day 4 doc review. | Release |
| L4 | Judge skips tarball fetch | High (60%) | Low | Pre-committed production eval JSON + HTML production panel. | Release |
| L5 | WSL/GDAL edge case on judge machine | Low (15%) | Low | CI uses ubuntu-latest as reference environment. | QA |

---

## Risk Heat Map (Likelihood × Impact)

```
Impact →
         Low      Medium    High      Critical
Likelihood
High     L4       M4,M5     —         —
Med      L3       M1-M3,H6  H3,H5     C3
Low      L1,L2    —         H4        C1,C2,C4
```

---

## Daily Risk Review Questions

1. Are production checkpoints located? (C1)
2. Do we have redistribution approval? (C2)
3. Is any experiment branch still open? (C3)
4. Does `make judge` pass on fresh clone? (H4)
5. Is `SVAMITVA_ARTIFACTS_URL` live and tested externally? (H2)

---

## Escalation Path

| Severity | Action | Timeline |
|----------|--------|----------|
| Critical | Stop all Track B work; war room | Immediate |
| High | Tech Lead decision; may slip freeze ≤4h | Same day |
| Medium | Log; fix in next validation window | ≤24h |
| Low | Backlog post-submission | — |

---

## Accepted Risks (Do Not Mitigate Further)

- Synthetic benchmark will not show strong Road/Water IoU — **accepted**; production eval is the answer.
- Bridge class remains at IoU 0.0 — **accepted**; documented non-operational.
- No hosted cloud demo URL — **accepted**; local demo + HTML pack sufficient for freeze.
