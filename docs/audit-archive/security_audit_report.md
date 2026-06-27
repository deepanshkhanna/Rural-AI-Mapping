# Security Audit Report

Date: 2026-06-07
Mode: Independent red-team review (evidence-only)

## Scope

- Code scanned: `src/`, `production/`, `demo_ui/`, `tools/`, root Python scripts.
- Pattern scan: secrets, credentials, unsafe deserialization, upload and API risk patterns.
- Excluded from pattern relevance: `.venv/` third-party packages.

## Critical Findings

1. Unauthenticated public inference endpoints
- Evidence: `production/api.py:49`, `production/api.py:54`, `production/api.py:59`, `production/api.py:67`, `production/api.py:88`
- Risk: Any caller can execute model inference and batch inference. This is a direct abuse surface for denial of service and cost exhaustion.

2. Unsafe checkpoint deserialization fallback is present
- Evidence: `src/security/checkpoints.py:61`
- Risk: The code path explicitly permits `torch.load(..., weights_only=False)` when override is enabled (`src/security/checkpoints.py:37-39`). This re-enables arbitrary pickle deserialization behavior if misconfigured.

3. API reads full upload into memory
- Evidence: `production/api.py:38-40`
- Risk: Per-request memory pressure up to 64MB payload before decode, with no request throttling. Concurrency spikes can exhaust memory.

4. No authentication, authorization, or rate limiting controls in production API
- Evidence: `production/api.py:17-94` (no auth middleware/dependencies, no rate limiting logic)
- Risk: Service-level abuse and inability to enforce least privilege.

5. Demo UI renders untrusted filename into HTML with `unsafe_allow_html=True`
- Evidence: `demo_ui/app.py:357`
- Risk: Filename-originated HTML injection risk in UI rendering context.

## High Findings

6. Broad exception suppression in postprocessing pipeline
- Evidence: `src/postprocessing.py:390-410`
- Risk: Silent failure of postprocessing steps can hide integrity issues and create non-deterministic output quality without alerting operators.

7. Production API coupled to demo module
- Evidence: `production/api.py:14`
- Risk: Security boundary is blurred; production service depends on presentation-layer package (`demo_ui`), increasing attack surface and maintenance risk.

8. Stateful global request counter is not concurrency-safe
- Evidence: `production/api.py:19`, `production/api.py:69-70`
- Risk: Under multi-worker/multi-thread deployment, metrics inconsistency and race-prone behavior.

9. Batch inference has no explicit file-count or cumulative-size guard
- Evidence: `production/api.py:88-94`
- Risk: Large multi-file requests can amplify CPU/GPU and memory pressure.

## Medium Findings

10. No explicit decompression-bomb guard for image parsing in API/UI
- Evidence: `production/api.py:43`, `demo_ui/app.py:273`
- Risk: Crafted images may trigger excessive decode resource usage.

11. Bind-on-all-interfaces documented as default run mode
- Evidence: `production/README.md:6`
- Risk: Increases accidental exposure risk if deployed on unmanaged networks.

## Secrets/Credentials Exposure Scan Result

- Direct hardcoded API key/token/password exposure in first-party repository code: Not found in current workspace scan.
- Residual risk: scan cannot prove historical Git history is clean.

## Security Score

Security: 3.8/10

Rationale:
- Positive: no direct plaintext API key exposure found in current files.
- Negative (dominant): no auth controls, unsafe deserialization fallback path exists, memory-abuse vectors, and silent exception swallowing in core pipeline.
