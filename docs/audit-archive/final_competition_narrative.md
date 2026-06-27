# Final Competition Narrative

This submission is a certified geospatial intelligence platform, not a single-run model demo.

What is operational now:
- Road segmentation analytics
- Built-Up Area segmentation analytics
- Water Body segmentation analytics
- Geospatially aligned outputs, API endpoints, and demo workflows

What is transparently constrained:
- Bridge segmentation is non-operational in current dataset/training regime.

Why this is competition-strong:
- Evidence-backed certification stack across evaluation, GIS, demo readiness, testing, security, and API operation.
- Reproducible and auditable artifact trail.
- Measurable stakeholder impact outputs at village level.
- Responsible limitation disclosure with a realistic detector-first roadmap.

Core message to judges:
- The platform is deployable for high-value infrastructure intelligence today.
- The bridge problem is formally closed for this cycle and responsibly positioned as a future detector module.

## Metric provenance (official claims)
- Source-of-truth file: `official_metrics_for_submission.md`.
- Evaluator: `run_calibrated_eval.py` + unified count-based metric computation.
- Checkpoint pipeline: `outputs/checkpoints/best_model.pth` (EMA epoch 43) + `outputs/checkpoints/latest_model.pth` (EMA epoch 80).
- Calibration: enabled (`outputs/optimal_bias.json`).
- TTA: enabled.
- Postprocessing: enabled.
- Date/source artifact: `outputs/calibrated_eval_results.json` (2026-06-07 00:37:33 +0530).
