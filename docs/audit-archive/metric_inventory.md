# Metric Inventory

Purpose: inventory every repository-authored artifact that reports, restates, or derives model metrics relevant to the submission.

Status legend:
- `canonical`: current reproducible artifact generated from current code/data.
- `derived`: summary or certification document derived from another artifact.
- `legacy`: older narrative/doc artifact with stale or unsupported numbers.
- `experimental`: bridge-only or controlled-experiment artifact; not comparable to the final submission path.

## Canonical Current Artifacts

| Artifact | Generated / modified | Metric family | Generator / origin | Status | Notes |
|---|---|---|---|---|---|
| `outputs/training_history.json` | 2026-04-15 04:11:38 +0530 | `val_iou`, `val_dice`, per-class IoU/Dice by epoch | `train.py` -> `validate_multiclass()` | `canonical` | Raw training-validation history. Epoch 43 is the best recorded raw-model validation point. |
| `outputs/checkpoints/best_model.pth` | 2026-04-15 03:32:12 +0530 | Stored checkpoint metadata (`epoch`, `best_iou`) | `train.py` best-checkpoint save path | `canonical` | File stores EMA weights in both `model_state_dict` and `ema_state_dict`. Metadata `best_iou` comes from raw-model validation, not a re-evaluation of the saved EMA payload. |
| `outputs/checkpoints/latest_model.pth` | 2026-04-15 04:11:39 +0530 | Stored checkpoint metadata (`epoch`, `best_iou`) | `train.py` latest-checkpoint save path | `canonical` | Raw model in `model_state_dict`, EMA in `ema_state_dict`. |
| `outputs/audit/audit_report.json` | 2026-06-07 00:40:01 +0530 | Clean per-class IoU/Precision/Recall/F1, confusion, confidence, fg_mIoU | `audit_model.py` | `canonical` | Current reproducible clean baseline for `best_model.pth` with no TTA and no postprocessing. |
| `outputs/audit/audit_report.txt` | 2026-06-07 00:40:01 +0530 | Same as JSON in human-readable form | `audit_model.py` | `canonical` | Text companion to `audit_report.json`. |
| `outputs/evaluation_report.json` | 2026-06-07 00:40:31 +0530 | Detection-style accuracy/precision/recall/F1, confusion, pixel accuracy | `evaluate_model_statistics.py` | `canonical` | Same checkpoint and validation grid as the clean audit, but a different reporting family. Does not report IoU directly. |
| `outputs/evaluation_report.txt` | 2026-06-07 00:40:31 +0530 | Same as JSON in human-readable form | `evaluate_model_statistics.py` | `canonical` | Stakeholder-style summary. |
| `outputs/optimal_bias.json` | 2026-06-06 22:32:35 +0530 | Chosen bias vector and cached-search metrics | `bias_search.py` / recovery flow | `canonical` | Intermediate calibration artifact used by the final calibrated pipeline. |
| `outputs/calibrated_eval_results.json` | 2026-06-07 00:37:33 +0530 | End-to-end per-class IoU/Precision/Recall/F1 and fg_mIoU | `run_calibrated_eval.py` | `canonical` | Final reproducible submission-pipeline metrics: ensemble + bias + TTA + postprocessing. |

## Derived Final-Submission Artifacts

| Artifact | Generated / modified | Metric family | Upstream source | Status | Notes |
|---|---|---|---|---|---|
| `outputs/recovery_reports/final_transformation_report.md` | 2026-06-06 22:32:35 +0530 | Final certified snapshot | `outputs/calibrated_eval_results.json` plus gate summaries | `derived` | Uses the calibrated end-to-end metrics as the final board-facing numbers. |
| `outputs/recovery_reports/bridge_recovery_report.md` | 2026-06-06 22:32:35 +0530 | Bridge end-to-end failure metrics | `outputs/calibrated_eval_results.json` | `derived` | Confirms bridge remains non-operational after calibration/postprocessing. |
| `outputs/recovery_reports/bridge_benchmark_report.md` | 2026-06-06 22:32:35 +0530 | Bridge benchmark + bias sweep summary | `outputs/calibrated_eval_results.json`, `bridge_bias_optimization_report.md` | `derived` | Bridge-specific summary only. |
| `outputs/recovery_reports/bridge_bias_optimization_report.md` | 2026-06-06 22:22:41 +0530 | Bridge bias sweep metrics | Cached logits optimization flow | `derived` | Not a submission metric source by itself. Shows bridge-only optimization behavior under extreme false positives. |
| `outputs/recovery_reports/evaluation_certification.md` | 2026-06-06 22:27:39 +0530 | Shared-evaluator consistency summary | `tools/evaluation_certification.py` | `derived` | Useful for consistency of the unified evaluator family, but not an independent reconciliation of legacy reports. |
| `executive_board_package.md` | 2026-06-07 00:30:02 +0530 | Final board-facing metric snapshot | `final_transformation_report.md` and recovery reports | `derived` | Submission summary only. |
| `final_submission_recommendation.md` | 2026-06-07 00:30:02 +0530 | Final board-facing metric references | Recovery reports | `derived` | Uses final calibrated/recovery metrics. |
| `judge_defense_book.md` | 2026-06-07 00:30:02 +0530 | Final defense numbers | Recovery reports | `derived` | Not a primary source. |
| `bridge_limitation_statement.md` | 2026-06-07 00:30:02 +0530 | Bridge limitation metrics | Bridge campaign and impossibility artifacts | `derived` | Narrative summary of bridge-only evidence. |

## Bridge Experimental Branches

These artifacts contain valid numbers, but they are not directly comparable to the final full-validation submission path.

| Artifact | Generated / modified | Metric family | Status | Why not submission source |
|---|---|---|---|---|
| `outputs/bridge_campaign/bridge_training_campaign.md` | 2026-06-07 00:07:19 +0530 | Campaign summary metrics | `experimental` | Campaign orchestration summary, not a final board-facing source. |
| `outputs/bridge_campaign/checkpoint_comparison.md` | 2026-06-07 00:07:19 +0530 | Full-val comparison across A-G bridge campaigns | `experimental` | Comparable within the bridge campaign only. Useful for ranking bridge variants, not for validating older docs. |
| `outputs/bridge_campaign/final_bridge_recovery_report.md` | 2026-06-07 00:07:19 +0530 | Baseline vs best bridge campaign | `experimental` | Bridge-focused branch summary. |
| `outputs/bridge_impossibility/bridge_impossibility_proof.md` | 2026-06-07 00:18:54 +0530 | Bridge signal and feasibility metrics | `experimental` | Scientific scope-closure document, not a full-model performance report. |
| `outputs/bridge_phase3/reports/bridge_experiments_report.md` | 2026-06-06 22:39:23 +0530 | Controlled bridge finetune metrics | `experimental` | Controlled bridge benchmark with different objective and protocol. |
| `outputs/bridge_phase3/reports/final_model_selection.md` | 2026-06-07 00:00:33 +0530 | Best bridge-experiment selection | `experimental` | Selects bridge experiments, not the final submission checkpoint. |
| `outputs/bridge_phase3/reports/bridge_architecture_comparison.md` | 2026-06-07 00:00:33 +0530 | Architecture comparison metrics | `experimental` | Controlled experimental branch only. |
| `outputs/bridge_phase3/reports/bridge_detector_option.md` | 2026-06-06 22:45:08 +0530 | Detector-option metrics | `experimental` | Roadmap support, not a current submission metric source. |
| `outputs/bridge_phase3/reports/bridge_root_cause_proof.md` | 2026-06-07 00:00:33 +0530 | Root-cause bridge metrics | `experimental` | Diagnostic branch only. |
| `outputs/bridge_phase3/reports/competition_readiness_report.md` | 2026-06-06 22:45:08 +0530 | Competition readiness summary | `experimental` | Experimental-branch summary, not final source of truth. |
| `outputs/bridge_phase3/reports/next_training_plan.md` | 2026-06-07 00:00:33 +0530 | Proposed next-step metric targets | `experimental` | Planning document only. |

## Legacy or Stale Narrative Artifacts

These files contain metrics, but they should not be used as current submission evidence without explicit re-generation.

| Artifact | Generated / modified | Metric family | Status | Why stale / unsafe |
|---|---|---|---|---|
| `README.md` | 2026-04-15 23:55:44 +0530 | Legacy narrative metrics | `legacy` | Replaced by official submission metrics table. |
| `docs/SYSTEM_OVERVIEW.md` | 2026-03-30 01:52:02 +0530 | Legacy overview metrics | `legacy` | Replaced by official submission metrics table. |
| `submission_document.md` | 2026-04-15 23:55:44 +0530 | Legacy narrative metrics | `legacy` | Replaced by official submission metrics table. |
| `demo_ui/README.md` | 2026-04-15 23:55:44 +0530 | Legacy demo metric references | `legacy` | Replaced by official submission metrics table. |
| `docs/demo_script.txt` | 2026-04-15 23:55:44 +0530 | Spoken metric narrative | `legacy` | Presentation script, not a primary source. |
| `docs/EVALUATION.md` | 2026-03-30 15:09:53 +0530 | Evaluation feature descriptions | `legacy` | Documentation of capability, not a canonical metric source. |
| `docs/TRAINING.md` | 2026-03-30 15:09:53 +0530 | Training/checkpoint metric descriptions | `legacy` | Documentation only. |
| `docs/ARCHITECTURE.md` | 2026-03-30 01:52:02 +0530 | Architecture references to mIoU | `legacy` | Documentation only. |

## Inventory Conclusion

Only the following artifacts are safe as current metric sources:

1. `outputs/training_history.json` for raw training-validation history.
2. `outputs/audit/audit_report.json` for clean single-checkpoint evaluation.
3. `outputs/evaluation_report.json` for stakeholder-style accuracy/precision/recall/F1 on the same clean checkpoint.
4. `outputs/calibrated_eval_results.json` for the final end-to-end submission pipeline.

Everything else should be treated as either a derived summary or a legacy/experimental branch.