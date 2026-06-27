# Win Probability Report

**Date:** 2026-06-15  
**Verdict class:** Strong Contender  
**Win probability (realistic judging):** Moderate — top quartile engineering, not top decile overall

---

## Current Position

After audit remediation, dominance implementation, and win-probability optimization:

| Layer | Status |
|-------|--------|
| Engineering | **Strong** — tiling, CRS, ensemble, API, CI, 64% test coverage |
| Evidence | **Strong** — HTML judge pack, SHA-256 manifest, survey intelligence |
| Synthetic verification | **Fixed** — FG mIoU **0.1989**, Built-Up IoU **0.7955** (was 0.0 due to bias bug) |
| Production benchmark | **External** — requires `SVAMITVA_ARTIFACTS_URL` release tarball |

The repository is no longer "unverifiable." It is **verifiable on synthetic benchmark** and **conditionally verifiable on production** if the team hosts authorized artifacts.

---

## Highest-Risk Weakness

**Production-trained checkpoints and real orthomosaic validation data are not in the repository.**

Judges cannot independently confirm historical headline metrics (e.g., FG mIoU 0.3871) from `git clone` alone. Competing teams with bundled or demonstrable production metrics will score higher on trustworthiness and ML leadership.

---

## Highest-Leverage Improvement

**Ship an authorized production benchmark release tarball** with:

- `outputs/checkpoints/best_model.pth`, `latest_model.pth`
- `outputs/optimal_bias.json`
- Subset of validation orthomosaics + shapefiles
- `benchmark/ARTIFACT_MANIFEST.json` with SHA-256 checksums

Generated via `scripts/package_production_release.sh`, distributed via `SVAMITVA_ARTIFACTS_URL`, verified via `scripts/verify_production_benchmark.sh`.

This single action closes the largest judge-scoring gap without fabricating evidence.

---

## Improvements Implemented

| # | Improvement | Evidence |
|---|-------------|----------|
| 1 | One-command judge workflow | `make judge`, `scripts/judge_verify.sh` |
| 2 | Synthetic zero-bias fix | `outputs/optimal_bias.json` → `[0,0,0,0,0]` |
| 3 | Full-raster verification scoring | `metrics.json` `scoring_scope: full_raster` |
| 4 | Production benchmark framework | `benchmark/`, `verify_production_benchmark.sh`, `package_production_release.sh` |
| 5 | Improved synthetic fixtures + 20-epoch demo train | Built-Up IoU 0.80 on val grid |
| 6 | Judge experience documentation | `JUDGE_EXPERIENCE.md` |
| 7 | Win analysis documentation | `WIN_ANALYSIS.md` |
| 8 | README judge quick start | Top of `README.md` |

---

## New Evidence Generated

| Artifact | Key value |
|----------|-----------|
| `evidence/judge_package/index.html` | Visual proof chain |
| `evidence/judge_package/metrics.json` | `fg_miou: 0.1989` |
| `evidence/judge_package/verification_manifest.json` | Per-file SHA-256 |
| `outputs/calibrated_eval_results.json` | `fg_miou: 0.2007`, git SHA, checkpoint hashes |
| `benchmark/ARTIFACT_MANIFEST.template.json` | Production release template |

Regenerate anytime: `make judge`

---

## Judge Friction Removed

| Before | After |
|--------|-------|
| Multiple undocumented scripts | `make judge` |
| Evidence showed 0.0 IoU (bias bug) | Honest ~0.20 FG mIoU |
| Top-left patch hid learnable classes | Full-raster scoring + center overlays |
| No production verify path | `verify_production_benchmark.sh` |
| Metrics contradicted README | Single provenance chain |

---

## Trustworthiness Improvements

1. **No fabricated metrics** — synthetic numbers regenerated from code
2. **Explicit synthetic vs production labeling** in HTML and docs
3. **Bridge non-operational** — unchanged, honest
4. **Bias provenance** — synthetic uses zero bias; production bias documented separately
5. **Archived legacy claims** — `docs/audit-archive/` only

---

## Competitive Advantages

| Advantage | vs higher-mIoU teams |
|-----------|---------------------|
| Survey intelligence layer | **Differentiator** if judges value decision support |
| One-command verification | **Differentiator** for time-limited judges |
| Geospatial engineering depth | **Parity or better** vs notebook submissions |
| Cryptographic evidence manifest | **Differentiator** for skeptical engineers |
| Raw mIoU on real data | **Disadvantage** without release tarball |

**Can advantages outweigh model performance?**  
Only if judges weight **system completeness, trust, and practical GIS output** over raw segmentation leaderboard. In a typical ML hackathon, **no** — mIoU remains the primary signal.

---

## Remaining Risks

1. Production artifacts not hosted → judges see synthetic-only metrics  
2. Water/Road classes near 0 IoU on synthetic benchmark → visual impression of partial failure  
3. No live hosted demo URL  
4. Checkpoint size (~100MB) blocks git inclusion without LFS/release hosting  
5. Competing teams may ship better documented dataset cards

---

## Final Question: Top 10%?

### Would this repository likely rank in the top 10% of submissions?

**NO**

### Evidence

1. **Synthetic FG mIoU ~0.20** vs expected winning submissions with **verified real-data mIoU 0.35–0.45+**
2. **Production benchmark not clone-verifiable** — trustworthiness dimension capped (~6.5/10)
3. **Positive factors** (engineering, judge pack, intelligence layer) place the repo in **upper-middle tier**, not top decile
4. Estimated composite **~7.6/10** (see `WIN_ANALYSIS.md`) — top 10% typically requires **8.5+** with verified benchmarks

### What single missing component most prevents this repository from becoming a likely winner?

**An authorized, checksum-verified production benchmark bundle (trained checkpoints + real validation orthomosaics) linked from the README so judges can reproduce headline segmentation metrics in one command.**

---

*Supporting documents: `WIN_ANALYSIS.md`, `JUDGE_EXPERIENCE.md`, `DOMINANCE_REPORT.md`, `IMPLEMENTATION_REPORT.md`*
