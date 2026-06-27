# Demo Risk Register

Context: Final judging live demonstration for frozen submission package. Scope is operational Road/Built-Up/Water analytics, with explicit bridge non-operational disclosure.

Scales:
- Probability: Low (<=20%), Medium (21-50%), High (>50%)
- Impact: Low (minor disruption), Medium (visible degradation), High (judge confidence or demo completion risk)

| ID | Risk event | Probability | Impact | Mitigation |
|---|---|---|---|---|
| 1 | Demo machine cannot start app due to environment mismatch | Medium (30%) | High | Use certified environment and dependency freeze before session; keep preflight checklist and startup smoke test completed before judges join. |
| 2 | API service fails health or readiness at demo start | Medium (25%) | High | Run endpoint preflight (`/health`, `/ready`) immediately before session; keep fallback restart command and validated port configuration prepared. |
| 3 | GPU unavailable and inference becomes too slow on CPU | Medium (35%) | Medium | Pre-detect compute mode and disclose expected throughput profile; keep smaller sample set ready for CPU fallback path. |
| 4 | Large upload exceeds enforced size limit and request is rejected | Medium (40%) | Medium | Keep pre-validated demo inputs below guardrail size; show this as intentional security behavior, not a failure. |
| 5 | Invalid file format provided live by judge | Medium (35%) | Medium | Use allowlisted file examples; if invalid file is tested, explain guardrail and recover with certified valid sample. |
| 6 | Bridge class output is challenged as failure | High (70%) | High | Proactively state bridge non-operational policy in opening minute; show transparent warning and pivot to operational classes and certified metrics. |
| 7 | Judge requests unsupported claim beyond two validation villages | High (60%) | High | Keep claims bounded to reported villages only; explicitly avoid extrapolation and emphasize governance honesty. |
| 8 | Metric inconsistency challenge between docs and spoken numbers | Medium (30%) | High | Read metrics from official table only and keep one printed reference sheet; avoid legacy metrics entirely. |
| 9 | UI confidence slider misuse leads to confusing masks | Medium (30%) | Medium | Reset to predefined default threshold profile during demo; explain threshold effect briefly and continue with baseline view. |
| 10 | Confidence map download fails due to browser permission/path issue | Low (20%) | Low | Preconfigure browser download permissions and keep visual-only fallback path without download dependency. |
| 11 | Network interruption during browser-based demo flow | Medium (25%) | Medium | Keep fully local/offline-capable demo sequence and local artifacts ready in same machine session. |
| 12 | Wrong image selected causing poor visual narrative | Medium (30%) | Medium | Use curated input set in fixed order with filenames and expected talking points rehearsed. |
| 13 | Judge asks for geospatial correctness proof on the spot | Medium (35%) | Medium | Keep GIS certification summary slide and key PASS statements ready; reference CRS/transform preservation evidence directly. |
| 14 | Judge asks for evaluation reproducibility proof immediately | Medium (35%) | High | Keep evaluation certification summary and zero-drift statement prepared; point to shared evaluator policy and source artifact timestamp. |
| 15 | Unexpected runtime warning appears in terminal/log | Medium (30%) | Low | Keep terminal hidden during narrative unless required; if shown, classify warning vs blocker and proceed with validated outputs. |
| 16 | Overfocus on Built-Up IoU weakness reduces confidence | High (55%) | Medium | Frame Built-Up as known performance asymmetry and emphasize precision/recall balance, operational fit, and policy-safe limitation disclosure. |
| 17 | Time overrun prevents covering deployment readiness evidence | Medium (40%) | High | Use strict run-of-show checkpoints (problem, metrics, trust stack, impact, limitation, close) with hard time caps per section. |
| 18 | Team member gives inconsistent answers under pressure | Medium (30%) | High | Assign single spokesperson for metrics and limitation policy; use prepared Q&A roles and handoff rules. |
| 19 | Judge asks for why this should win versus stronger raw-model teams | High (65%) | High | Lead with governance moat: evaluation integrity, GIS correctness, testing, security, API readiness, and transparent risk management. |
| 20 | Closing recommendation sounds defensive instead of decisive | Medium (35%) | High | End with clear call: deploy Road/Built-Up/Water now, disclose bridge limitation transparently, and execute detector-first roadmap next. |

## Top 5 Priority Risks

1. Bridge challenge escalation (ID 6)
2. Win-justification pressure (ID 19)
3. Unsupported extrapolation trap (ID 7)
4. Metric inconsistency slip (ID 8)
5. Time overrun of trust evidence (ID 17)

## Live Demo Control Checklist

- Confirm app startup and endpoint readiness before judges enter.
- Keep official metrics table visible to presenter.
- Open with scope policy: Road/Built-Up/Water operational, bridge non-operational.
- Use pre-curated input sequence with expected outcomes.
- Reserve final minute for deployment recommendation and limitation honesty.