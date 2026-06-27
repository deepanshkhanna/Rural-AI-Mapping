# Data Leakage Report

Date: 2026-06-07
Mode: Independent red-team review (evidence-only)

## Scope

- Reviewed geodata presence in workspace, metadata, config, and generated artifacts.
- Reviewed location identifiers, machine-path leakage, and dataset governance signals.

## Critical Findings

1. Raw geospatial assets present in repository workspace at massive scale
- Evidence: workspace footprint is `50G`; large files include `data/...*.tif`, `data/...*.ecw`, `Test/...*.tif`, `demo_ui/assets/samples/*.tif`.
- Risk: High accidental exposure risk and non-compliance exposure if this workspace is mirrored or archived without strict controls.

2. Village/location identifiers embedded in configuration
- Evidence: `config/platform_config.v1.json:11-22`
- Risk: Explicit place identifiers materially increase re-identification and sensitive-location disclosure risk.

3. Internal filesystem paths leaked in generated artifacts
- Evidence: `outputs/bridge_campaign/campaign_results.json` and multiple `outputs/...` reports include `/home/dk/ml_projects/iit_hackathon/...` absolute paths.
- Risk: Environment fingerprint leakage and infrastructure metadata exposure.

## High Findings

4. Geospatial dataset naming and partition metadata exposed in public-facing docs
- Evidence: `README.md:43`, `config/platform_config.v1.json:11-22`
- Risk: Reveals operational dataset partition details and village-level scope boundaries.

5. Quarantine/corrupt data samples still retained in workspace
- Evidence: `data/quarantine/corrupt_tiffs/...`
- Risk: Data retention governance weakness; risk of accidental reuse and data quality contamination.

6. EPSG and geospatial operational assumptions are explicitly disclosed
- Evidence: `config/platform_config.v1.json:44-46`
- Risk: Not a vulnerability by itself, but contributes to operational footprint disclosure.

## Medium Findings

7. Demo samples are real geospatial TIFFs
- Evidence: `demo_ui/assets/samples/*.tif`
- Risk: Demo distribution can unintentionally carry real location data.

8. Submission and impact reports include detailed place-specific metrics
- Evidence: `stakeholder_impact_report.md` (village-specific metrics and names)
- Risk: Could require explicit legal basis and data-sharing approvals depending on governance policy.

## Data Governance Score

Data Governance: 3.2/10

Rationale:
- Positive: no direct personal identifiers observed in scanned core source files.
- Negative (dominant): extensive raw geodata retention, location-identifiable naming, and machine-path leakage in generated artifacts.
