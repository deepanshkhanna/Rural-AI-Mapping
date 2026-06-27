# Repository Knockdown List

Date: 2026-06-07
Ranking basis: severity x impact x likelihood (red-team bias)

Scale:
- Severity: Critical / High / Medium
- Impact: Very High / High / Medium
- Likelihood: High / Medium / Low
- Fix effort: Low / Medium / High / Very High
- Priority: P0 / P1 / P2

## Top 25 Issues

1. Unauthenticated production inference endpoints
- Severity: Critical
- Impact: Very High
- Likelihood: High
- Evidence: `production/api.py:49-94`
- Risk: unrestricted service abuse
- Fix effort: Medium
- Priority: P0

2. Unsafe deserialization fallback path exists
- Severity: Critical
- Impact: Very High
- Likelihood: Medium
- Evidence: `src/security/checkpoints.py:61`, `src/security/checkpoints.py:37-39`
- Risk: code execution via untrusted checkpoint if override enabled
- Fix effort: Medium
- Priority: P0

3. Full upload read into memory per request
- Severity: High
- Impact: Very High
- Likelihood: High
- Evidence: `production/api.py:38-40`
- Risk: memory exhaustion under concurrent load
- Fix effort: Medium
- Priority: P0

4. Batch endpoint lacks aggregate request guardrails
- Severity: High
- Impact: High
- Likelihood: High
- Evidence: `production/api.py:88-94`
- Risk: amplified DoS surface
- Fix effort: Medium
- Priority: P0

5. Silent exception suppression in core postprocessing
- Severity: High
- Impact: High
- Likelihood: High
- Evidence: `src/postprocessing.py:390-410`
- Risk: hidden correctness regressions
- Fix effort: Low
- Priority: P1

6. Production depends on demo package
- Severity: High
- Impact: High
- Likelihood: High
- Evidence: `production/api.py:14`
- Risk: architecture boundary violation
- Fix effort: Medium
- Priority: P1

7. Workspace contains 50G including raw geospatial assets
- Severity: High
- Impact: Very High
- Likelihood: High
- Evidence: workspace size and large-file inventory
- Risk: data leakage and operational instability
- Fix effort: Very High
- Priority: P1

8. Location-identifiable village names embedded in config
- Severity: High
- Impact: High
- Likelihood: High
- Evidence: `config/platform_config.v1.json:11-22`
- Risk: location leakage/compliance exposure
- Fix effort: Medium
- Priority: P1

9. Absolute machine paths leaked in generated artifacts
- Severity: High
- Impact: Medium
- Likelihood: High
- Evidence: `outputs/bridge_campaign/campaign_results.json` and related outputs
- Risk: environment fingerprint leakage
- Fix effort: Low
- Priority: P1

10. No CI workflow scaffold detected
- Severity: High
- Impact: High
- Likelihood: High
- Evidence: no `.github/`
- Risk: no automated quality/security gates
- Fix effort: Medium
- Priority: P1

11. No container baseline for deployment portability
- Severity: High
- Impact: High
- Likelihood: Medium
- Evidence: no `Dockerfile`
- Risk: environment drift
- Fix effort: Medium
- Priority: P1

12. Dependency versions are not pinned
- Severity: High
- Impact: High
- Likelihood: High
- Evidence: `requirements.txt:2-41`
- Risk: non-reproducible runtime and supply-chain variance
- Fix effort: Medium
- Priority: P1

13. Architecture documentation is stale on class taxonomy
- Severity: High
- Impact: High
- Likelihood: High
- Evidence: `docs/ARCHITECTURE.md:7`, `docs/ARCHITECTURE.md:71`
- Risk: audit and implementation confusion
- Fix effort: Low
- Priority: P1

14. Demo instructions stale on class taxonomy
- Severity: High
- Impact: Medium
- Likelihood: High
- Evidence: `docs/demo_instructions.md:74-82`
- Risk: user/operator misinterpretation
- Fix effort: Low
- Priority: P1

15. No explicit legal license file
- Severity: High
- Impact: Medium
- Likelihood: Medium
- Evidence: no `LICENSE*` file found
- Risk: legal/procurement blocker
- Fix effort: Low
- Priority: P1

16. No explicit compliance/governance policy document for data handling
- Severity: High
- Impact: High
- Likelihood: Medium
- Evidence: no dedicated legal/compliance policy artifact detected
- Risk: government deployment approval risk
- Fix effort: Medium
- Priority: P1

17. Production metrics endpoint is too shallow for operations
- Severity: Medium
- Impact: High
- Likelihood: High
- Evidence: `production/api.py:59-64`
- Risk: weak incident diagnosis capability
- Fix effort: Medium
- Priority: P2

18. Request counter uses mutable global state
- Severity: Medium
- Impact: Medium
- Likelihood: High
- Evidence: `production/api.py:19`, `production/api.py:69-70`
- Risk: inaccurate telemetry under concurrency
- Fix effort: Low
- Priority: P2

19. Demo UI renders uploaded filename in HTML context
- Severity: Medium
- Impact: Medium
- Likelihood: Medium
- Evidence: `demo_ui/app.py:357`
- Risk: UI injection surface
- Fix effort: Low
- Priority: P2

20. Evaluation script includes hardcoded baseline comparator values
- Severity: Medium
- Impact: Medium
- Likelihood: High
- Evidence: `run_calibrated_eval.py:94`, `run_calibrated_eval.py:97`
- Risk: metric confusion and operator error
- Fix effort: Low
- Priority: P2

21. Testing coverage scope is narrow relative to code surface
- Severity: Medium
- Impact: Medium
- Likelihood: High
- Evidence: `pytest.ini:2`
- Risk: regressions in untested modules
- Fix effort: Medium
- Priority: P2

22. Print-centric observability instead of structured logging
- Severity: Medium
- Impact: Medium
- Likelihood: High
- Evidence: widespread `print(...)` usage across `src/` and tools
- Risk: poor production diagnostics
- Fix effort: Medium
- Priority: P2

23. Quarantine and corrupt geodata retained in active workspace
- Severity: Medium
- Impact: Medium
- Likelihood: High
- Evidence: `data/quarantine/corrupt_tiffs/*`
- Risk: accidental contamination and retention policy concerns
- Fix effort: Medium
- Priority: P2

24. Bind-all-interfaces run command documented without hardening context
- Severity: Medium
- Impact: Medium
- Likelihood: Medium
- Evidence: `production/README.md:6`
- Risk: accidental exposure in unmanaged environments
- Fix effort: Low
- Priority: P2

25. Submission/report document sprawl increases source-of-truth ambiguity
- Severity: Medium
- Impact: Medium
- Likelihood: High
- Evidence: numerous top-level markdown artifacts with overlapping scope
- Risk: audit and maintenance burden
- Fix effort: Medium
- Priority: P2
