# Judge Defense Book

Scope policy:
- Bridge segmentation feasibility is closed for this submission cycle.
- All answers are grounded in repository evidence.

Metric claim policy:
- Board-facing metric claims must use `official_metrics_for_submission.md`.

Metric provenance for official claims:
- Evaluator: `run_calibrated_eval.py` + unified count-based metric computation.
- Checkpoint pipeline: `outputs/checkpoints/best_model.pth` (EMA epoch 43) + `outputs/checkpoints/latest_model.pth` (EMA epoch 80).
- Calibration: enabled (`outputs/optimal_bias.json`).
- TTA: enabled.
- Postprocessing: enabled.
- Date/source artifact: `outputs/calibrated_eval_results.json` (2026-06-07 00:37:33 +0530).

## 50 difficult questions with evidence-backed answers

1. Q: Why should judges trust your evaluation numbers?
A: Evaluation certification shows zero drift across certified entry points (max IoU delta 0.000000000000), proving shared evaluator consistency.

2. Q: Is geospatial alignment preserved in outputs?
A: GIS certification reports CRS and transform match PASS with alignment score 1.00 on certified prediction files.

3. Q: Are you hiding bridge failure?
A: No. Bridge limitation is explicitly documented with measured evidence and included as a submission constraint.

4. Q: What proves bridge segmentation is currently non-operational?
A: Final bridge recovery report shows Bridge IoU/F1 remained 0.0000 in baseline and best configuration.

5. Q: Why is bridge difficult in this dataset?
A: Bridge share of foreground is 0.046184%, indicating severe class signal scarcity.

6. Q: What does confusion say about bridge behavior?
A: On GT bridge pixels, only 0.318632% is predicted as bridge; most is background/road/water.

7. Q: Did you keep retraining until something worked for bridge?
A: No further bridge retraining was performed after impossibility conclusion.

8. Q: What is your strongest operational performance evidence?
A: Final transformation snapshot: Road IoU 0.5555, Built-Up IoU 0.1615, Water IoU 0.8315, fg_mIoU 0.3871.

9. Q: Is this only a notebook demo or a deployable system?
A: Production API endpoints are implemented and smoke-tested: /health, /ready, /metrics, /infer, /infer-batch.

10. Q: Do tests actually pass?
A: Yes. 17 passed, 0 failed, total coverage 91.48%.

11. Q: Is there a security review?
A: Yes. Security review status PASS with 0 findings.

12. Q: How do you control unsafe model loading?
A: Secure checkpoint loading path is used and validated by platform security constraints.

13. Q: How do you ensure upload safety in demo/API?
A: Allowlist extensions + max upload size (64 MB) + invalid image handling with explicit 400 responses.

14. Q: Is demo readiness independently validated?
A: Yes, demo readiness certification is PASS and includes runtime path validation.

15. Q: What about long-running scripts not finishing in CI-like sessions?
A: Execution validation explicitly separates smoke validation from long jobs and reports both states transparently.

16. Q: Why not remove bridge entirely from UI?
A: We keep it visible with explicit warning to preserve transparency and avoid hidden limitations.

17. Q: What changed in the final demo polish?
A: Added tunable overlay alpha, confidence thresholding, confidence map download, and explicit non-operational bridge warning.

18. Q: How do you defend class imbalance concerns?
A: We quantify imbalance using dataset truth and information content reports.

19. Q: Is your geospatial validation limited to one CRS?
A: No. Certified outputs cover EPSG:32644 and EPSG:4326 with transform preservation.

20. Q: What is the practical throughput profile?
A: Benchmark reports ~20.02 patches/s GPU vs ~0.29 patches/s CPU for 768x768 forward.

21. Q: Did torch.compile help?
A: Yes. Latency reduced from 24.485 ms to 20.589 ms; throughput increased from 40.842 to 48.570 ips.

22. Q: Do you have evidence of reproducibility?
A: Demo readiness and dependency validation reports certify environment reproducibility and successful import validation.

23. Q: Are data quality issues known and managed?
A: Dataset health report identifies 2 unreadable rasters; handling is documented with skip logic and remediation reports.

24. Q: Why choose hybrid platform framing?
A: It maximizes judged value by combining certified segmentation, GIS correctness, API readiness, and governed bridge roadmap.

25. Q: Why not present only Road/Built-Up/Water and ignore bridge entirely?
A: We preserve scientific transparency and future extensibility via documented detector roadmap.

26. Q: How do you avoid overclaiming from two validation villages?
A: We report exact village-level metrics and do not extrapolate unsupported performance claims.

27. Q: How is stakeholder impact quantified?
A: Per village: road coverage, built-up coverage, infrastructure density, and land-use indicators are computed and reported.

28. Q: Give one actionable village insight.
A: Nadala has infrastructure density 16.8543% and built/water pressure 19.8451, indicating high settlement intensity.

29. Q: Give another actionable village insight.
A: Nagul cluster shows low infrastructure density (0.0574%) with relatively higher water share, supporting water-sensitive planning.

30. Q: Is this system audit-friendly?
A: Yes. Artifact-driven governance with certification reports, JSON outputs, and reproducible scripts supports audit trails.

31. Q: Are metrics consistent between campaign and final impossibility docs?
A: Yes for bridge non-recovery conclusion; both independently indicate bridge IoU/F1 operational failure.

32. Q: Why include detector feasibility if not trained now?
A: It is framed as roadmap feasibility, not current production claim, and is evidence-backed by measured instance dimensions.

33. Q: What is detector feasibility evidence?
A: 100% of extracted bridge instances exceed min-dimension thresholds (16/24/32 px).

34. Q: How do you defend low bridge silhouette but high AUC in feature analysis?
A: We report both and avoid overinterpretation; final decision is anchored in end-to-end validation failure, not one embedding metric.

35. Q: Is your architecture locked to one model family?
A: No. Model factory supports architecture switching; current certified path uses DeepLabV3Plus.

36. Q: What if judges ask for bridge output live?
A: We show output with explicit warning that bridge is non-operational and excluded from success claims.

37. Q: Did you pass geospatial and evaluation gates simultaneously?
A: Yes. Both certifications are PASS.

38. Q: Is there formal production readiness evidence?
A: Production readiness report states PARTIAL due to bridge quality blocker, while API/runtime gates pass.

39. Q: Why is partial readiness acceptable for competition?
A: Because submission narrative is re-scoped to certified operational capabilities and explicit known limitation disclosure.

40. Q: Are there unresolved critical security issues?
A: No. Security findings are zero.

41. Q: How is fairness in claims maintained?
A: Every major claim in final package is tied to a measurable artifact path.

42. Q: How do you prevent regression after submission?
A: Use certification gateboard (evaluation/GIS/demo/testing/security) as release criteria for future increments.

43. Q: Why should government stakeholders trust adoption readiness?
A: Certified geospatial correctness, reproducible environment checks, and API readiness reduce operational risk.

44. Q: What is your strongest competitive moat versus typical hackathon demos?
A: Integrated governance stack: testing coverage, security review, GIS certification, evaluation certification, and API validation.

45. Q: What is your weakest point today?
A: Bridge class performance remains non-operational.

46. Q: What is your mitigation strategy?
A: Scope control now (Road/Built-Up/Water) plus detector-first bridge roadmap with data expansion gates.

47. Q: Can this scale beyond demo images?
A: Sliding-window inference, geospatial output validation, and API endpoints are already in place for staged scaling.

48. Q: What evidence supports demo stability?
A: Demo certification PASS and runtime startup validation in execution reports.

49. Q: What single recommendation do you want judges to remember?
A: This is a credible, deployable geospatial intelligence platform with transparent limitations and a governed roadmap.

50. Q: What is the final submission position?
A: Submit the current platform with explicit bridge limitation and detector roadmap (see final submission recommendation).

## Evidence references
- outputs/bridge_impossibility/bridge_impossibility_proof.md
- outputs/bridge_impossibility/bridge_confusion_report.md
- outputs/bridge_impossibility/bridge_information_content_report.md
- outputs/bridge_impossibility/bridge_detector_feasibility_report.md
- outputs/bridge_campaign/final_bridge_recovery_report.md
- outputs/recovery_reports/final_transformation_report.md
- outputs/recovery_reports/evaluation_certification.md
- outputs/recovery_reports/gis_certification_report.md
- outputs/recovery_reports/demo_certification_report.md
- outputs/recovery_reports/demo_readiness_certification.md
- outputs/recovery_reports/testing_coverage_report.md
- outputs/recovery_reports/security_review_report.md
- outputs/recovery_reports/production_api_report.md
- outputs/recovery_reports/performance_optimization_report.md
- outputs/recovery_reports/performance_benchmark_report.md
