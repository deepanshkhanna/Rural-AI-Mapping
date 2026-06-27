# Python Engineering Report

Date: 2026-06-07
Mode: Independent red-team review (evidence-only)

## Scope

- Reviewed maintainability, error handling, typing discipline, testability, and dependency control in Python codebase.

## High Findings

1. Silent error swallowing in production-relevant path
- Evidence: `src/postprocessing.py:390-410` uses repeated `except Exception: pass`.
- Risk: hidden correctness regressions and non-diagnosable output drift.

2. Extensive print-based instrumentation over structured logging
- Evidence: multiple modules use `print(...)` for operational state (`src/datasets/unified_dataset.py`, `train.py`, `run_calibrated_eval.py`, `tools/*`).
- Risk: weak observability and poor production telemetry integration.

3. Broad `except Exception` usage in dataset and validation paths
- Evidence: `src/datasets/unified_dataset.py:276-277`, `src/datasets/unified_dataset.py:416-417`, `src/data_validation/validator.py:76`, `src/data_validation/validator.py:111`.
- Risk: overbroad exception handling can suppress actionable root causes.

4. Tight coupling from production API into demo package
- Evidence: `production/api.py:14` imports from `demo_ui.inference_wrapper`.
- Risk: separation-of-concerns violation and fragile dependency graph.

## Medium Findings

5. Inconsistent type rigor across modules
- Evidence: some typed dataclasses/configs (`src/config/platform_config.py`) coexist with large untyped scripts and dict-heavy pipelines.
- Risk: static analysis coverage is limited; refactor risk increases.

6. Monolithic scripts with mixed concerns at repository root
- Evidence: root-level `train.py`, `audit_model.py`, `evaluate_model_statistics.py`, `bias_search.py`, `run_calibrated_eval.py`.
- Risk: maintenance cost and onboarding complexity.

7. Global mutable state in API (`REQUEST_COUNT`)
- Evidence: `production/api.py:19`, `production/api.py:69-70`.
- Risk: concurrency correctness and metric fidelity issues.

## Positive Notes

- Centralized runtime config model exists (`src/config/platform_config.py`).
- Security-focused checkpoint wrapper exists (`src/security/checkpoints.py`) despite fallback risk.

## Python Engineering Score

Python Engineering: 5.1/10

Rationale:
- Core structure exists but is undermined by silent exception handling, observability gaps, and coupling issues.
