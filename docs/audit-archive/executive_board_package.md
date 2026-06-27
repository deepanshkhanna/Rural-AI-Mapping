# Executive Board Package

## Problem
Rural geospatial intelligence pipelines often fail in production due to weak evaluation governance, geospatial misalignment, low reproducibility, and limited deployment readiness.

## Solution
This project delivers a certified geospatial intelligence platform for operational classes:
- Road
- Built-Up Area
- Water Body

Bridge segmentation is explicitly constrained as non-operational in this cycle, with a detector-first roadmap documented for future increments.

## Evidence of credibility
- Evaluation certification: PASS, max IoU drift across certified paths = 0.000000000000.
- GIS certification: PASS, CRS and transform preservation confirmed.
- Demo certification: PASS.
- Security review: PASS with 0 findings.
- Testing quality: 17 passed, 0 failed, 91.48% coverage.
- Production API readiness: PASS with validated health/ready/metrics/infer endpoints.

## Metrics snapshot
- fg_mIoU: 0.3871
- Road IoU: 0.5555
- Built-Up IoU: 0.1615
- Water IoU: 0.8315
- Bridge IoU: 0.0000 (non-operational constraint)

## Metric provenance
- Evaluator: `run_calibrated_eval.py` + unified count-based metric computation.
- Checkpoint pipeline: `outputs/checkpoints/best_model.pth` (EMA epoch 43) + `outputs/checkpoints/latest_model.pth` (EMA epoch 80).
- Calibration status: Enabled (`outputs/optimal_bias.json`).
- TTA status: Enabled.
- Postprocessing status: Enabled.
- Date/source artifact: `outputs/calibrated_eval_results.json` (2026-06-07 00:37:33 +0530).

## Limitation (explicit)
Bridge segmentation is currently not feasible with available dataset signal and present setup.
Measured evidence:
- Bridge share of foreground: 0.046184%
- GT bridge pixels predicted as bridge: 0.318632%
- Bridge IoU/F1 remained 0.0000 across campaign variants

## Stakeholder impact (validation villages)
- Nadala (66.47 ha): infrastructure density 16.8543%, building density 28.9459/ha, built/water pressure 19.8451.
- Nagul cluster (3055.74 ha): infrastructure density 0.0574%, building density 0.0923/ha, built/water pressure 0.4184.

These outputs support planning prioritization, settlement-pressure monitoring, and water-sensitive governance decisions.

## Deployment roadmap
- Pilot: controlled operational deployment for Road/Built-Up/Water with certification gates.
- District: standardized batch reporting and QA workflows.
- State: governance dashboards and versioned release gates.
- National: federated data governance and audited output framework.

## Recommendation to judges and stakeholders
Adopt the platform for operational geospatial analytics now (Road/Built-Up/Water), with transparent bridge limitation disclosure and a detector-first bridge roadmap in the next program increment.

## Primary evidence files
- outputs/recovery_reports/final_transformation_report.md
- outputs/recovery_reports/evaluation_certification.md
- outputs/recovery_reports/gis_certification_report.md
- outputs/recovery_reports/demo_certification_report.md
- outputs/recovery_reports/testing_coverage_report.md
- outputs/recovery_reports/security_review_report.md
- outputs/recovery_reports/production_api_report.md
- outputs/bridge_impossibility/bridge_impossibility_proof.md
- outputs/final_submission_data/stakeholder_impact_metrics.csv
