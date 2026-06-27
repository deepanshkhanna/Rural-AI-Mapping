# RECOVERY VERIFICATION REPORT

**Date:** 2026-06-16  
**Type:** Dry-run recovery on current machine  
**Verdict:** **PASS**

## Simulated Scenario

Fresh recovery from frozen `production_release/` artifacts (no reliance on pre-existing `outputs/checkpoints/`).

## Steps Executed

| Step | Command / Action | Result |
|------|------------------|--------|
| 1. Deploy checkpoints | `cp production_release/checkpoints/*.pth outputs/checkpoints/` | PASS |
| 2. Deploy calibration | `cp production_release/bias/optimal_bias.json outputs/optimal_bias.json` | PASS |
| 3. Verify checkpoint hashes | SHA-256 match MANIFEST | PASS |
| 4. Run evaluation | `python run_calibrated_eval.py --require-bias --skip-validation` | PASS |
| 5. Compare metrics | vs `epoch_71_results.json` | PASS |

## Metric Reproduction

| Metric | Certified | Reproduced | Match |
|--------|-----------|------------|-------|
| FG mIoU | 0.4809 | 0.4809 | YES |
| Road IoU | 0.4356 | 0.4356 | YES |
| Built-Up IoU | 0.7415 | 0.7415 | YES |
| Water IoU | 0.7466 | 0.7466 | YES |
| Bridge IoU | 0.0000 | 0.0000 | YES |

Eval time: 161.6s on CUDA (PyTorch 2.12.0+cu130).

## Checkpoint Hashes (verified at load)

| Checkpoint | SHA-256 |
|------------|---------|
| best_model.pth | `8675e06ae0584bd5105b88f2e8356777d85d7eaeb585c4b4381a087162f7d892` |
| latest_model.pth | `f8f45947be59825fbb6addc54c75d748f1722d57bb636299bfe9a1da51ca1aa7` |

## Calibration Hash

`optimal_bias.json`: `4ff3321bb6aa06c46e834f844ea0e3a1b574e806bd0515c4531b71e51d0e788e`

## Environment

- Python 3.10.12
- Git SHA at eval: `350a6d541b3c0857d8c1d557b8906298481e7963`
- Validation patches: 598 (NADALA + NAGUL)
- Results artifact: `outputs/calibrated_eval_results.json`

## Clone Recovery (reviewer)

```bash
git clone https://github.com/deepanshkhanna/iit_hackathon.git
cd iit_hackathon
git checkout v1.0-certified
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp production_release/checkpoints/*.pth outputs/checkpoints/
cp production_release/bias/optimal_bias.json outputs/optimal_bias.json
# Deploy data/ per DATASET_CARD.md
python run_calibrated_eval.py --require-bias
```

## Conclusion

**Recovery verification PASS.** Certified metrics are fully reproducible from frozen production assets.
