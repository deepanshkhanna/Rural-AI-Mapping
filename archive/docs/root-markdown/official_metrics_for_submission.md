# Official Metrics For Submission

## Rule

Board-facing metrics must come **only** from a committed `outputs/calibrated_eval_results.json` produced by:

```bash
make judge                           # synthetic: train + eval + evidence (recommended for judges)
bash scripts/reproduce.sh            # synthetic CI path (eval only if checkpoints exist)
# OR
bash scripts/fetch_artifacts.sh && python run_calibrated_eval.py --require-bias
```

Do not cite numbers from README tables, archived audit reports, or hardcoded script literals.

## Artifact Structure

`outputs/calibrated_eval_results.json` contains:

- `provenance` — git SHA, checkpoint SHA-256, bias vector, split, timestamps
- `baseline` — metrics without postprocessing (computed same run)
- `calibrated` — metrics with full pipeline (ensemble + bias + TTA + postprocess)

## Historical Note

Pre-remediation metrics (e.g. FG mIoU 0.3871) were sourced to a non-existent artifact and are **retired**. They are preserved only in `docs/audit-archive/` for audit traceability. Regenerate all claims from the reproducible pipeline above.

## Synthetic vs Production

| Path | Config | Purpose |
|---|---|---|
| `scripts/reproduce.sh` | `platform_config.synthetic.json` | CI verification; proves pipeline executes |
| Production eval | `platform_config.v1.json` + release artifacts | Real submission metrics |

Synthetic metrics are not submission claims — they validate engineering correctness only.
