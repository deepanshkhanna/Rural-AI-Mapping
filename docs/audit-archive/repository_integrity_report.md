# Repository Integrity Report

Date: 2026-06-07
Scope: Post-remediation verification (no fixes applied)

## Verification Checks

1. Broken references
- Method: Parsed markdown links across repository docs (excluding `.venv`) and verified local targets.
- Result: PASS
- Evidence: `BROKEN_COUNT=0`

2. Missing files
- Method: Verified required remediation input reports exist and checked referenced remediation file paths.
- Result: PASS (for repository file references)
- Note: Command snippets inside backticks were excluded from missing-file classification.

3. Orphan documentation
- Method: Inbound-reference scan across markdown corpus.
- Result: FAIL
- Evidence: `ORPHAN_COUNT=31` (includes multiple audit/remediation docs and generated docs that are not linked by other docs)
- Example orphan docs: `security_remediation_report.md`, `repository_reaudit_report.md`, `docs/ARCHITECTURE.generated.md`

4. Deleted dependencies
- Method: Validated dependency manifest structure and runtime dependency health.
- Result: PASS
- Evidence:
  - `requirements.txt` present with 24 pinned packages (`UNPINNED_COUNT=0`)
  - `python -m pip check` returned `No broken requirements found.`

## Integrity Verdict

- Overall: PARTIAL PASS
- Blocking integrity issue: orphan documentation remains substantial and impacts navigability and traceability.
