# Bridge Limitation Statement

## Scientific position
Bridge segmentation is currently non-feasible under the present dataset signal and current segmentation setup. This is treated as an established constraint in final submission scope.

## Why bridge failed (measured)
- Campaign A-G result remained at Bridge IoU=0.0000 and Bridge F1=0.0000, including best configuration.
- Bridge share of foreground signal is 0.046184%.
- On GT bridge pixels, current best checkpoint predicts Bridge for only 0.318632% of pixels.
- GT bridge pixels are dominated by non-bridge outputs (83.754615% background, 8.055892% road).

## Evidence chain
- outputs/bridge_campaign/final_bridge_recovery_report.md
- outputs/bridge_impossibility/bridge_information_content_report.md
- outputs/bridge_impossibility/bridge_confusion_report.md
- outputs/bridge_impossibility/bridge_impossibility_proof.md

## Why additional segmentation training is unlikely to help (current setup)
- Multiple training variants already failed to move validation bridge metrics above zero.
- Information content remains severely imbalanced relative to Road/Built-Up/Water.
- Current confusion profile indicates systemic bridge suppression, not stochastic underfitting.

## Future data collection strategy
- Increase bridge-positive annotated coverage density across diverse geographies, widths, and adjacency conditions.
- Add bridge-focused hard negatives (road-over-water without bridge label ambiguity).
- Tighten bridge annotation protocol for boundary consistency in bridge-road transition zones.
- Introduce explicit bridge quality gates before model certification.

## Future detector strategy
- Treat bridge as a dedicated detector/instance problem in next increment.
- Feasibility evidence: 100% of extracted bridge instances exceed 16/24/32 px minimum dimension in the audit set; detector feasibility score is 0.8875 versus current segmentation bridge recall proxy of 0.318632%.
- Reference: outputs/bridge_impossibility/bridge_detector_feasibility_report.md

## Submission policy
- Bridge outputs are disclosed transparently as non-operational.
- Judged value is concentrated on certified, deployable Road/Built-Up/Water geospatial intelligence outcomes.
