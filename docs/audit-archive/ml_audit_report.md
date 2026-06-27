# ML Audit Report

Date: 2026-06-07
Mode: Independent red-team review (evidence-only)

## Scope

- Reviewed dataset handling, leakage controls, reproducibility discipline, evaluation consistency, and monitoring readiness.

## Critical Findings

1. Bridge class remains operationally failed in official metrics
- Evidence: official package reports Bridge IoU/F1 = 0.0000.
- Risk: major model capability gap for one declared taxonomy class.

2. Evaluation script embeds baseline constants that appear stale/non-authoritative
- Evidence: `run_calibrated_eval.py:94`, `run_calibrated_eval.py:97` hardcodes baseline values including `Built-Up Area: 0.6530`.
- Risk: confusion risk and metric miscommunication in engineering operations.

## High Findings

3. Reproducibility is not fully hardened despite seed setup
- Evidence: seed function exists (`train.py:145-151`), but DataLoader in calibrated eval uses workers (`run_calibrated_eval.py:81-82`) without explicit deterministic worker strategy in that script.
- Risk: run-to-run variability under different runtime conditions.

4. Heavy dependence on postprocessing with failure suppression
- Evidence: `src/postprocessing.py:390-410`.
- Risk: model quality and postprocess quality become hard to disentangle; silent failures may bias perceived model behavior.

5. Dataset and split identifiers exposed in config/docs
- Evidence: `config/platform_config.v1.json:11-22`, `README.md:43`.
- Risk: governance and leakage concern; weak dataset abstraction boundary.

## Medium Findings

6. No explicit model-monitoring package for drift/quality after deployment
- Evidence: no dedicated runtime monitoring module or alerting pipeline found in repository structure.
- Risk: weak post-deployment quality control.

7. Experiment lineage is distributed across many artifacts, not one immutable tracker
- Evidence: many output reports and tools; no single experiment registry or metadata service.
- Risk: traceability overhead and human error risk.

## Positive Notes

- Unified evaluator function exists (`src/evaluation/unified_evaluator.py`).
- Config-driven class and split loading exists (`src/config/platform_config.py`).

## ML Engineering Score

ML Engineering: 5.0/10

Rationale:
- Strength in evaluation formalism and config centralization, but major class failure, reproducibility gaps, and postprocess opacity lower confidence.
