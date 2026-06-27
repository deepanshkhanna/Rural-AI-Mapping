# RELEASE INTEGRITY AUDIT

**Audited:** 2026-06-15 18:46 UTC

## Scope

`production_release/` frozen bundle for certified epoch_71 ensemble.

## Required artifacts

| Category | Path | Status |
|----------|------|--------|
| Best checkpoint | `checkpoints/best_model.pth` (306 MB, ep 71) | PASS |
| Latest checkpoint | `checkpoints/latest_model.pth` (408 MB, ep 80) | PASS |
| Bias calibration | `bias/optimal_bias.json` | PASS |
| Manifest + checksums | `MANIFEST.json` | PASS |
| Winner metrics | `metrics/epoch_71_results.json` | PASS |
| Candidate metrics | `metrics/epoch_{33,69,80}_results.json` | PASS |
| Certification reports | `reports/*.md` (5 files) | PASS |

## Checksum verification

All **7** manifest entries verified SHA-256 on disk. **0 mismatches.**

| File | SHA-256 (prefix) |
|------|------------------|
| checkpoints/best_model.pth | `8675e06ae0584bd5…` |
| checkpoints/latest_model.pth | `f8f45947be59825f…` |
| bias/optimal_bias.json | `4ff3321bb6aa06c4…` |
| metrics/epoch_71_results.json | `14f53a12e3332ac1…` |

## Gaps

- None blocking submission. Operational copies also exist under `outputs/checkpoints/` and `outputs/certification/` (not part of frozen bundle).

## Verdict

**RELEASE INTEGRITY: PASS**
