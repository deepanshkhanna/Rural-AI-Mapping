# REPRODUCIBILITY AUDIT

**Run:** 2026-06-15 18:46 UTC

## Procedure

1. Verified `production_release/` checksums (PASS).
2. Deployed frozen artifacts:
   - `production_release/checkpoints/*` → `outputs/checkpoints/`
   - `production_release/bias/optimal_bias.json` → `outputs/optimal_bias.json`
3. Ran: `python run_calibrated_eval.py --require-bias --skip-validation`
4. Compared to certified `epoch_71_results.json`.

## Results

| Metric | Certified | Reproduced | Match |
|--------|-----------|------------|-------|
| FG mIoU | 0.4809 | 0.4809 | YES |
| Road IoU | 0.4356 | 0.4356 | YES |
| Built-Up IoU | 0.7415 | 0.7415 | YES |
| Water IoU | 0.7466 | 0.7466 | YES |
| Bridge IoU | 0.0000 | 0.0000 | YES |

Eval time: 156.88s on CUDA.

## Environment

- Python 3.10.12
- PyTorch 2.12.0+cu130
- Git SHA: `350a6d541b3c0857d8c1d557b8906298481e7963`

## Reviewer commands

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp production_release/checkpoints/*.pth outputs/checkpoints/
cp production_release/bias/optimal_bias.json outputs/optimal_bias.json
python run_calibrated_eval.py --require-bias
```

Requires real GeoTIFF + shapefile data under `data/` per `config/platform_config.v1.json`.

## Verdict

**REPRODUCIBILITY: PASS** — certified metrics reproduced exactly from frozen release.
