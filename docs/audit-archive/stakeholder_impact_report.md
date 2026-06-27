# Stakeholder Impact Report

Data basis:
- Validation villages from platform_config: 28996_NADALA_ORTHO and NAGUL_450171_MADASE_450172_GHOTPAL_450137_ORTHO.
- Metrics computed from geospatial village extents and source class geometries.
- Metric table artifact: outputs/final_submission_data/stakeholder_impact_metrics.csv

## Village-level outputs

### 1) 28996_NADALA_ORTHO (PB)
- Area: 66.47 ha
- Road coverage: 4.0053%
- Built-up coverage: 12.8490%
- Water coverage: 0.6475%
- Infrastructure density (Road + Built-up): 16.8543%
- Built-up polygon count: 1924
- Building density: 28.9459 buildings/ha
- Water bodies: 3 (4.5134 per km2)
- Land-use indicator (built/water surface pressure): 19.8451

### 2) NAGUL_450171_MADASE_450172_GHOTPAL_450137_ORTHO (CG-3)
- Area: 3055.74 ha
- Road coverage: 0.0224%
- Built-up coverage: 0.0349%
- Water coverage: 0.0835%
- Infrastructure density (Road + Built-up): 0.0574%
- Built-up polygon count: 282
- Building density: 0.0923 buildings/ha
- Water bodies: 8 (0.2618 per km2)
- Land-use indicator (built/water surface pressure): 0.4184

## Cross-village interpretation for governance use
- Settlement intensity differs by orders of magnitude between the two validation villages (28.9459 vs 0.0923 buildings/ha), indicating materially different service-planning profiles.
- Nadala exhibits high impervious pressure (infrastructure density 16.8543%) and high built-to-water pressure (19.8451), suitable for prioritizing drainage resilience and urban service capacity checks.
- Nagul-Madase-Ghotpal shows sparse built and road footprint with higher relative water share, suitable for water-body preservation and low-density mobility planning.

## Government stakeholder value translation
- Panchayat planning: objective baseline for village-level infrastructure distribution and land-use pressure.
- Rural works prioritization: road and settlement density support segment-level prioritization for connectivity interventions.
- Water governance: water-body coverage and density provide transparent indicators for resource and resilience planning.
- Monitoring and auditability: all metrics are reproducible from geospatial evidence and report artifacts.

## Certification context
- Evaluation consistency: PASS (outputs/recovery_reports/evaluation_certification.md)
- Geospatial correctness: PASS (outputs/recovery_reports/gis_certification_report.md)
- Demo readiness: PASS (outputs/recovery_reports/demo_certification_report.md)
