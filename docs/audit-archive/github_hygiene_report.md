# GitHub Hygiene Report

Date: 2026-06-07
Mode: Independent red-team review (evidence-only)

## Scope

- Reviewed ignore policy, repository cleanliness signals, file footprint, and tracked/untracked drift.

## Critical Findings

1. Severe repository/workspace bloat
- Evidence: workspace size `50G`; many files >20MB including TIFF/ECW, checkpoints, and caches.
- Risk: Cloning, CI, security scanning, and review workflows become fragile and expensive.

2. Major working tree hygiene breakdown
- Evidence: `git status --short | wc -l` = `52` changed/untracked entries.
- Risk: High accidental commit risk and poor release reproducibility.

3. Ignore policy and actual workspace state are inconsistent
- Evidence: `.gitignore` excludes `data/`, `Test/`, `outputs/`, but large artifacts are present in workspace.
- Risk: Operational confusion and accidental policy bypass in manual workflows.

## High Findings

4. No CI workflow repository scaffolding detected
- Evidence: no `.github/` directory found.
- Risk: No automated policy gate for tests, linting, security checks, or artifact controls.

5. No container or build standardization files detected
- Evidence: no `Dockerfile`, no `Makefile`, no deployment orchestration YAML.
- Risk: inconsistent local execution behavior and weak onboarding repeatability.

6. Git tracked-file count is unexpectedly low relative to workspace complexity
- Evidence: `git ls-files | wc -l` = `37`.
- Risk: repository state appears fragmented between tracked and local-only artifacts.

## Medium Findings

7. Output and recovery artifacts dominate local footprint
- Evidence: numerous `outputs/...` binaries and reports.
- Risk: local confusion and accidental stale-data use.

8. Mixed naming conventions and archival residue across root-level markdowns
- Evidence: large set of similarly themed top-level report files.
- Risk: documentation discoverability and maintenance burden.

## GitHub Hygiene Score

GitHub Hygiene: 2.9/10

Rationale:
- Positive: `.gitignore` contains relevant categories.
- Negative (dominant): very large workspace, high dirty state, missing CI/deployment scaffolding, and fragmented tracked-vs-local asset state.
