# DevOps Audit Report

Date: 2026-06-07
Mode: Independent red-team review (evidence-only)

## Scope

- Reviewed environment setup, dependency control, deployment portability, observability, and operational hardening.

## Critical Findings

1. No containerization baseline
- Evidence: no `Dockerfile` detected.
- Risk: environment drift and weak deployment portability.

2. No CI/CD or policy-gate workflows detected
- Evidence: no `.github/` directory.
- Risk: no automated enforcement for tests, security scan, lint, or release checks.

3. Dependencies are not version-pinned for reproducible builds
- Evidence: `requirements.txt:2-41` uses lower-bounded ranges (`>=`) only.
- Risk: non-deterministic installs and difficult incident rollback.

## High Findings

4. Production service exposed on all interfaces in documented run command
- Evidence: `production/README.md:6` uses `--host 0.0.0.0`.
- Risk: accidental network exposure if deployed without perimeter controls.

5. API operational controls are minimal
- Evidence: `production/api.py:49-94` includes no auth, no throttling, no request budgeting.
- Risk: abuse and instability under untrusted traffic.

6. Metrics/observability are limited
- Evidence: `production/api.py:59-64` exposes only request count and uptime.
- Risk: insufficient telemetry for production incident response.

## Medium Findings

7. Testing scope in pytest configuration is narrow relative to total code surface
- Evidence: `pytest.ini:2` only covers selected packages.
- Risk: untested areas can regress unnoticed.

8. No infrastructure-as-code or deployment manifests found
- Evidence: no YAML manifests, no Makefile, no orchestrator definitions.
- Risk: manual deployment variance.

## DevOps Score

DevOps: 3.4/10

Rationale:
- Basic runnable service exists, but deployment hardening and reproducible operations controls are substantially incomplete.
