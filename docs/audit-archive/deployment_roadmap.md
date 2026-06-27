# Deployment Roadmap

## Stage 1: Pilot (selected blocks / panchayats)
Requirements:
- Operational scope fixed to Road/Built-Up/Water outputs.
- Certified runtime stack and API deployment baseline.
- District-level geospatial ingestion SOP.

Risks:
- Misinterpretation of bridge output if not clearly constrained.
- Data heterogeneity across pilot geographies.

Data needs:
- Fresh orthomosaic samples for pilot geography.
- Ground verification for road/building/water indicators.

Expected improvements:
- Faster local planning cycles via consistent village metrics.
- Early governance feedback loop for model quality and UI workflow.

## Stage 2: District roll-out
Requirements:
- Standardized batch inference and report generation pipeline.
- Monitoring and alerting on API service and output artifact integrity.
- District QA protocol for geospatial alignment checks.

Risks:
- Throughput bottlenecks on CPU-only deployments.
- Variable CRS/source quality in district data streams.

Data needs:
- District-wide imagery refresh cadence.
- Structured validation sample registry for quarterly audits.

Expected improvements:
- District-level prioritization based on infrastructure density and land-use indicators.
- Higher operational confidence through repeat certification gates.

## Stage 3: State scale
Requirements:
- Multi-district orchestration and workload scheduling.
- Governance dashboards for quality gates (evaluation, GIS, security, tests).
- Versioned model/report release management.

Risks:
- Operational drift if certification gates are bypassed.
- Increased support burden without standardized MLOps SOP.

Data needs:
- State harmonization of geospatial metadata conventions.
- Expanded training/validation assets for non-operational classes (bridge roadmap).

Expected improvements:
- State-wide comparability of village infrastructure indicators.
- Policy-level trend monitoring across regions.

## Stage 4: National program
Requirements:
- Federated data governance and security controls.
- National API and batch processing service reliability targets.
- Independent audit process for model and geospatial outputs.

Risks:
- Cross-state data inconsistency and legal constraints.
- Demand spikes affecting inference service reliability.

Data needs:
- National imagery ingestion standards.
- Continuous annotation program for future bridge detector module.

Expected improvements:
- Nationwide geospatial intelligence baseline for rural infrastructure planning.
- Transparent, auditable reporting framework usable by central and state stakeholders.

## Bridge roadmap policy across all stages
- Do not claim bridge segmentation as operational until acceptance gates are passed.
- Prioritize detector-first bridge module after data expansion and annotation protocol hardening.
