# Metrics Defense

**Trigger question:** *"Your mIoU is lower than another team's."*

**Rules:** Never evade. Never exaggerate. Never cite unreproducible numbers. Never attack competitors.

---

## The Response (Memorize)

> "You're right that on the synthetic verification benchmark in our evidence pack, foreground mIoU is about **0.20**. We show that number prominently and we label it synthetic — it exists to prove our pipeline runs end-to-end with cryptographic provenance, not to claim production village performance.
>
> We deliberately did not cite production mIoU in the submission because we cannot redistribute the trained checkpoints and validation orthomosaics under current data terms. Any number we cannot let you reproduce, we do not put in front of you.
>
> Where we differentiate is what happens **after** segmentation: our system produces a **survey intelligence report** — road access percentages, settlement fragmentation, explainability review zones, and written field recommendations. A higher-mIoU mask is still a mask. We deliver the briefing a Panchayat survey officer would use to decide where to send field teams.
>
> If you'd like to see the value layer, the executive summary and recommendations are at the top of our judge evidence pack — or I can show them live in the demo in thirty seconds."

**Duration:** 45–60 seconds. Then **stop talking about mIoU** and open the intelligence artifact.

---

## Why This Works (Judge Psychology)

| Principle | How we apply it |
|-----------|-----------------|
| **Acknowledge** | We do not dispute 0.20; we state it precisely |
| **Reframe scope** | Synthetic = pipeline verification, not production claim |
| **Integrity signal** | We refused to cite unreproducible production mIoU |
| **Pivot to strength** | Survey intelligence is implemented and openable |
| **No competitor attack** | "They may score higher on leaderboard" — concede the axis, claim a different one |

---

## Supporting Evidence (If Pressed)

| Claim | Source | Value |
|-------|--------|-------|
| Synthetic FG mIoU | `evidence/judge_package/metrics.json` | 0.1989 |
| Built-Up IoU (synthetic) | Same | 0.7955 |
| Reproducibility | `make judge` | Regenerates metrics + SHA-256 manifest |
| Provenance | `verification_manifest.json` | Per-file checksums |
| No production claim in README | `README.md` | Leads with survey intelligence |

---

## What NOT To Say

| Forbidden | Why |
|-----------|-----|
| "Our real mIoU is 0.39" | Not reproducible from submission |
| "Synthetic doesn't matter" | Judges saw the table; dismissive |
| "mIoU is the wrong metric" | Sounds defensive without pivot |
| "The other team cheated / overfit" | Unprofessional; no evidence |
| "Built-Up is 0.80 so we're fine" | Cherry-picking; Road/Water are 0 |

---

## Visual Pivot (Immediately After Verbal Response)

1. Open `evidence/judge_package/index.html` → **Survey Intelligence** card (top of page)
2. Read one recommendation aloud — e.g. road access / field verification
3. Optional: Streamlit → Survey Intelligence expander

**Goal:** Judge memory shifts from "0.20 mIoU" to "they produce officer briefings."

---

## If Judge Insists on Production Numbers

> "I cannot ask you to trust a production number I cannot hand you. What I can hand you is the verification chain: clone the repo, run `make judge`, inspect the SHA-256 manifest, and see the intelligence report generated from the same pipeline that would run on village orthomosaics when authorized data is available. Our packaging scripts for a production benchmark bundle are in the repo — the blocker is data release approval, not engineering."

**Artifact:** `scripts/package_production_release.sh`, `benchmark/ARTIFACT_MANIFEST.template.json`

---

## One-Line Fallback (Under Time Pressure)

> "Lower synthetic mIoU, honest labeling, but we deliver what SVAMITVA actually needs — survey intelligence, not just a mask."
