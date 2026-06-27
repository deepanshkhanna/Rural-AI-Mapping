# PRODUCTION ASSET FREEZE REPORT

**Date:** 2026-06-16  
**Status:** **FROZEN**

## Scope

All artifacts under `production_release/` are locked for V1. Checksums generated at freeze time.

## Artifact Inventory

| Path | Size | SHA-256 |
|------|------|---------|
| `MANIFEST.json` | 1,450 B | `cf6eb3cb6da88119e2c37306034b1132d68df0d186cdc3a15dbf8219c2626cf5` |
| `bias/optimal_bias.json` | 533 B | `4ff3321bb6aa06c46e834f844ea0e3a1b574e806bd0515c4531b71e51d0e788e` |
| `checkpoints/best_model.pth` | 305.8 MB | `8675e06ae0584bd5105b88f2e8356777d85d7eaeb585c4b4381a087162f7d892` |
| `checkpoints/latest_model.pth` | 407.9 MB | `f8f45947be59825fbb6addc54c75d748f1722d57bb636299bfe9a1da51ca1aa7` |
| `metrics/epoch_33_results.json` | 3,504 B | `1ed83b7810619890011ede8427c397de283bcb15301d7fd2b0345a5919c4f3a5` |
| `metrics/epoch_69_results.json` | 3,489 B | `f1af3f40bddf52191af2e2bddf86ff27d457b786d7538be3997249a26eb8f488` |
| `metrics/epoch_71_results.json` | 6,188 B | `14f53a12e3332ac15f81d663ff5a0a83b141093b5d6b0fab4928feae1c82d4c4` |
| `metrics/epoch_80_results.json` | 3,458 B | `14b3728fb3f9af80f91a26360892bc3ad87d4414a31681cb8b976549294a9d25` |
| `reports/FINAL_MODEL_CERTIFICATION.md` | 1,781 B | `c75093b5cb1036109c5ac6b0edb38a3612f65e39eac83ccf40affa9718a27486` |
| `reports/FINAL_MODEL_RANKING.md` | 1,319 B | `2ff59724bcf5898caca44dc9db73bf824de39a9edbffb5634025b2350aedd6ec` |
| `reports/PRODUCTION_RELEASE_MANIFEST.md` | 988 B | `e3e9a127b94b8bc2c47b586ee05543d30bb676cf57f618f4a65334b2c608e0dc` |
| `reports/SVAMITVA_FINAL_PRODUCTION_DECISION.md` | 1,749 B | `24f3a37cb22ab0362f51b5f16d45a12494eea748105538dcb79b22108def59ea` |
| `reports/WINNER_STRESS_REPORT.md` | 864 B | `5aef3d81baf763e001949300fc34c818c243fdd4771002a495a5cd449c02fd10` |

**Total artifacts:** 13 files (~714 MB)

## Checksum Storage

- Master file: `production_release/checksums/SHA256SUMS.txt`
- JSON manifest: `production_release/checksums/checksum_manifest.json`

## MANIFEST Cross-Check

Original `MANIFEST.json` (7 tracked binary artifacts): **7/7 PASS** against freeze checksums.

## Modification Policy

```
production_release/  → READ ONLY after v1.0-certified
SUBMISSION_PACKAGE/  → READ ONLY after v1.0-certified
```

Any change requires a new certification cycle and new release tag.

## Verification Command

```bash
cd production_release/checksums
sha256sum -c SHA256SUMS.txt
```

(Paths relative to `production_release/`.)
