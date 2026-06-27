# Presentation Audit

Judge-perspective scoring of the SVAMITVA submission for a 7-minute presentation + 5-minute Q&A.

---

## Dimension Scores

| Dimension | Score (1–10) | Assessment |
|-----------|--------------|------------|
| **Problem clarity** | **9** | SVAMITVA land mapping bottleneck is concrete and government-relevant. Lead with "property cards need maps; maps need infrastructure extraction." |
| **Innovation** | **7** | Architecture is proven (DeepLabV3Plus), not novel. Innovation is in the **full pipeline**: ensemble + calibration + TTA + geospatial postprocessing + survey intelligence. Do not oversell "novel architecture." |
| **Technical depth** | **9** | Strong: certified 4-candidate matrix, rejected alternatives with metrics, checksums, reproducible eval. Risk: too much detail in 7 min — curate ruthlessly. |
| **Evidence** | **9** | FG mIoU 0.4809 is checksum-locked. HTML evidence bundle. Per-village stress. Weak point: Bridge 0.0 — address proactively. |
| **Deployment readiness** | **8** | Docker API, offline capable, security controls. Gap: no live pilot metrics. Show `docker compose up` in backup demo. |
| **Business value** | **8** | Clear digitization cost savings narrative. Strengthen with one concrete example: "X hours manual → Y minutes automated + review." |
| **Government value** | **9** | Direct SVAMITVA alignment: roads, settlements, water for property surveys. Survey intelligence beyond masks differentiates from pure ML teams. |

**Overall presentation strength: 8.4 / 10**

---

## What Judges Will Remember (If You Do It Right)

1. **0.4809 FG mIoU** — one number, stated once, with "reproducible from code"
2. **Village-held-out validation** — scientific rigor signal
3. **Live HTML evidence** — not just slides
4. **Honest about NAGUL** — builds trust
5. **Survey intelligence** — not just another segmentation model

## What Judges Will Forget (Avoid)

- Training hyperparameter details (batch size, accumulation)
- Experiment archive names (exp04, exp09)
- Loss function mathematics
- Parameter count (unless asked)

---

## Top 10 Slides That Matter

| # | Slide Title | Purpose | Key Content | Time |
|---|-------------|---------|-------------|------|
| 1 | **The SVAMITVA Bottleneck** | Hook | Drone surveys produce orthomosaics; manual digitization is slow; property cards wait on maps | 30 sec |
| 2 | **Our Solution** | Problem → approach | Automated segmentation of Road, Built-Up, Water from orthomosaics + survey intelligence | 30 sec |
| 3 | **Dataset & Validation** | Rigor | 6 train / 2 val villages; 598 held-out patches; CRS-validated geodata | 45 sec |
| 4 | **Architecture** | Technical credibility | DeepLabV3Plus-ResNet50 diagram; 768 px; 5 classes | 45 sec |
| 5 | **Inference Pipeline** | Differentiation | Ensemble → calibration → TTA → postprocessing flowchart | 60 sec |
| 6 | **Results** | Evidence | FG mIoU 0.4809 table; per-class IoU; per-village NADALA/NAGUL | 60 sec |
| 7 | **What We Tested & Rejected** | Defensibility | SegFormer 0.4038; marathon regression; "we measure, not assume" | 45 sec |
| 8 | **Survey Intelligence** | Beyond ML | Connectivity, fragmentation, review zones, field recommendations | 45 sec |
| 9 | **Deployment** | Production signal | Docker API screenshot; offline; checksums; `make judge` | 45 sec |
| 10 | **Impact & Ask** | Close | Faster maps → faster property cards; human-in-the-loop; reproducible today | 30 sec |

**Total: ~7 minutes** (leaves 30 sec buffer)

---

## Slides to Cut or Merge

| Cut | Reason |
|-----|--------|
| Training loss equations | Q&A only |
| Full experiment history | One "rejected alternatives" slide suffices |
| Team intro > 15 sec | Judges care about the system |
| Generic AI/ML market slides | Not relevant |
| Bridge class details | Mention as non-operational in one bullet |

---

## Presentation Risks

| Risk | Mitigation |
|------|------------|
| Demo fails live | Pre-open `evidence/judge_package/index.html`; screen recording backup |
| Judge asks about NAGUL | "We report it: FG 0.4124. Domain shift is why we need more diverse training data." |
| Judge says Road IoU is low | "0.64 recall — we find roads. Precision is the challenge at 1–2 px width." |
| Running over time | Slides 7 and 8 are droppable if needed; never cut slide 6 (Results) |
| Overselling Bridge | Never mention Bridge IoU unless asked; say "non-operational, not claimed" |

---

## Recommended Narrative Arc

```
Problem (pain) → Approach (credibility) → Pipeline (differentiation) →
Results (evidence) → Honest limits (trust) → Deployment (ready) → Impact (why it matters)
```

**Golden rule:** Every claim on a slide must have a file path in speaker notes.

---

## Pre-Presentation Checklist

- [ ] `evidence/judge_package/index.html` opens offline
- [ ] Streamlit demo tested (`streamlit run demo_ui/app.py`)
- [ ] Docker API starts (`docker compose up`)
- [ ] Results slide matches `production_release/metrics/epoch_71_results.json` exactly
- [ ] Speaker notes link to `submission/JUDGE_QA_MASTER.md` for Q&A
- [ ] No slide cites metrics from `archive/`
