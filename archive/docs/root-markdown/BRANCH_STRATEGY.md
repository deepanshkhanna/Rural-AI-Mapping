# BRANCH STRATEGY

**Effective:** 2026-06-16 (V1 certified release)

## Branches

| Branch | Purpose | Receives experimental commits? |
|--------|---------|-------------------------------|
| `main` | Default integration; carries V1 freeze + release docs | No (after freeze) |
| `stable/v1` | Immutable certified V1 snapshot | **Never** |
| `experiment/main` | All future research and high-risk work | **Yes** |

## Rules

### `stable/v1`

- Created from V1 freeze commit
- Tagged `v1.0-certified`
- **Never** receives experimental commits
- Hotfixes to V1 only with explicit certification re-run and new tag (e.g. `v1.0.1`)

### `experiment/main`

- Branched from V1 freeze commit
- All model changes, new architectures, fine-tuning, ensembles
- May diverge freely from stable metrics
- Results do not affect certified V1 unless promoted through full certification

### `main`

- Points to V1 freeze at release time
- Future merges from `experiment/main` only after certification gate passes

## Workflow

```
v1.0-certified (tag)
       │
       ├── stable/v1  (frozen forever)
       │
       ├── main       (integration, starts at V1)
       │
       └── experiment/main  (all future research)
```

## Promotion Gate

An experiment on `experiment/main` may merge to `main` / replace V1 only when:

1. Reproducible (`run_calibrated_eval.py` exact reproduction)
2. Benchmarked (beats `BASELINE_SNAPSHOT.md` on FG mIoU and per-class IoU)
3. Certified (full production certification pipeline)
4. Documented (new MODEL_CARD, BENCHMARK_CARD, certification report)

## Protected Paths (all branches)

Do not modify on any branch without explicit V2 certification:

- `production_release/`
- `SUBMISSION_PACKAGE/`

Experimental code belongs in `research/`.
