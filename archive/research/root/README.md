# Research / Experimental Zone

**Status:** All work after V1 certified release (`v1.0-certified`) belongs here.

## Policy

| Zone | Rule |
|------|------|
| `research/` | Experimental — may change freely |
| `production_release/` | **FROZEN** — do not modify |
| `SUBMISSION_PACKAGE/` | **FROZEN** — do not modify |

Anything inside `research/` is experimental. Results here do **not** replace the certified V1 model unless they pass full certification:

1. Reproducible evaluation (`run_calibrated_eval.py`)
2. Benchmarked against `BASELINE_SNAPSHOT.md`
3. Certified via the production certification pipeline
4. Demonstrably better than V1 on held-out validation evidence

## Branch

Future experiments commit to `experiment/main`, never to `stable/v1`.

## Baseline

Compare all experiments against `BASELINE_SNAPSHOT.md` at repository root.
