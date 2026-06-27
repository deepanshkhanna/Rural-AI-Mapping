# Architecture Audit Report

Date: 2026-06-07
Mode: Independent red-team review (evidence-only)

## Scope

- Reviewed modularity, separation of concerns, coupling, extensibility, and maintainability.

## High Findings

1. Production-to-demo dependency inversion
- Evidence: `production/api.py:14` imports from `demo_ui.inference_wrapper`.
- Risk: production service is architecturally dependent on presentation-layer module.

2. Repository root mixes core runtime, experiments, governance docs, and tooling scripts
- Evidence: many root-level scripts and board documents alongside runtime code.
- Risk: high cognitive load and weak boundary clarity between product, research, and reporting.

3. Postprocessing is a single broad pipeline with silent fail-open behavior
- Evidence: `src/postprocessing.py:374-410`.
- Risk: hidden coupling between model output quality and chained heuristic transforms.

## Medium Findings

4. Strong central config model exists but not uniformly enforced across all entry points
- Evidence: `src/config/platform_config.py` exists, yet multiple scripts include local constants/behavior.
- Risk: drift potential across scripts.

5. Tooling and operational concerns are tightly co-located
- Evidence: `tools/` scripts interact deeply with checkpoints, outputs, and runtime modules.
- Risk: accidental use of experimental flows in operational contexts.

6. Architecture docs are not synchronized with active platform schema
- Evidence: mismatch between `docs/ARCHITECTURE.md` and `config/platform_config.v1.json`.
- Risk: design ambiguity for maintainers.

## Positive Notes

- `src/` contains meaningful domain separation (`config`, `datasets`, `evaluation`, `inference`, `security`, `training`).
- Unified evaluator and security checkpoint wrapper are architecturally valuable components.

## Architecture Score

Architecture: 5.4/10

Rationale:
- Baseline modular structure exists, but separation-of-concerns and boundary discipline are weakened by coupling and fail-open postprocess behavior.
