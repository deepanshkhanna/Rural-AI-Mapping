# PRODUCTION RELEASE MANIFEST

Certified at: 2026-06-15T18:41:08.274158+00:00

## Winner

`epoch_71` ensemble frozen under `production_release/`.

## File checksums (SHA-256)

| File | SHA-256 |
|------|---------|
| `bias/optimal_bias.json` | `4ff3321bb6aa06c4…` |
| `checkpoints/best_model.pth` | `8675e06ae0584bd5…` |
| `checkpoints/latest_model.pth` | `f8f45947be59825f…` |
| `metrics/epoch_33_results.json` | `1ed83b7810619890…` |
| `metrics/epoch_69_results.json` | `f1af3f40bddf5219…` |
| `metrics/epoch_71_results.json` | `14f53a12e3332ac1…` |
| `metrics/epoch_80_results.json` | `14b3728fb3f9af80…` |

## Policy

**Do not overwrite** files in `production_release/`. Future training runs must write to separate paths.

## Reproduction

```bash
# Load frozen checkpoints + bias from production_release/
python run_calibrated_eval.py  # after symlinking or copying release artifacts to outputs/
```

Per-candidate evidence: `outputs/certification/epoch_*_results.json`
