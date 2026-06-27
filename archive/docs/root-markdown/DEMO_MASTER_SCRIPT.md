# Demo Master Script — 3 Minutes

**Goal:** Judge leaves remembering **survey intelligence**, not mIoU.  
**Prerequisite:** Streamlit running (`streamlit run demo_ui/app.py`) OR judge HTML open as backup.  
**Backup:** If live demo fails → `evidence/judge_package/index.html` (no GPU needed).

**Total time:** 180 seconds. Every second justified.

---

## Pre-Flight (Before Judge Enters)

- [ ] Tab 1: `evidence/judge_package/index.html` (Survey Intelligence card visible)
- [ ] Tab 2: Streamlit on `localhost:8501`
- [ ] Synthetic sample ready (or pre-run inference cached)
- [ ] Do NOT open metrics table first

---

## Screen-by-Screen Script

### 0:00–0:20 | Act 1 — Problem (Judge HTML or slide)

| | |
|--|--|
| **Screen** | Title: "SVAMITVA Village Survey Intelligence" or static slide |
| **Objective** | Establish government problem, not ML problem |
| **Talking point** | "Panchayats receive drone orthomosaics. Survey officers need to know: which settlements lack road access, where settlement is fragmented, and where humans must verify before records update. A colored mask does not answer that." |
| **Expected reaction** | Nods — problem is concrete |

---

### 0:20–0:50 | Act 2 — Why masks fail (Streamlit upload OR static overlay)

| | |
|--|--|
| **Screen** | Streamlit: upload synthetic ortho OR show pre-loaded overlay (RGB + mask) |
| **Objective** | Show segmentation exists but is insufficient |
| **Talking point** | "We do extract roads, buildings, and water — geospatially correct, tiled for full orthomosaics. But stopping here leaves the officer staring at pixels. Watch what the system produces next." |
| **Expected reaction** | "OK, they have segmentation" — transitional |

**Do NOT:** Mention mIoU. Do NOT show metrics sidebar first.

---

### 0:50–1:40 | Act 3–4 — Intelligence + Recommendations (PRIMARY)

| | |
|--|--|
| **Screen** | Streamlit: **Survey Intelligence Report** expander (`expanded=True`) OR judge HTML primary card |
| **Objective** | **Peak judge impact** — this is the money screen |
| **Talking point** | "This is the survey officer's briefing pack. Total area, structure count, road access percentage, fragmentation index, confidence split — and written recommendations." |
| **Read aloud** | One recommendation from list — e.g. *"Only X% of built-up area is within 50 meters of mapped roads. Field verification recommended for remote settlements."* |
| **Expected reaction** | "This is different from other teams" — lean in |

**Seconds 1:20–1:40:** Point to review zones / explainability line: "81% flagged for review — here are the zones where we send field teams first."

---

### 1:40–2:10 | Act 5 — Government value (API curl OR architecture one-liner)

| | |
|--|--|
| **Screen** | README snippet or terminal: `POST /survey-report` OR mention FastAPI |
| **Objective** | Deployability — GIS departments integrate, not just demo |
| **Talking point** | "Same JSON via API for state GIS integration. Docker, secure checkpoints, georeferenced GeoTIFF output. Streamlit is visualization; the core is production API." |
| **Expected reaction** | Engineering credibility without drowning in code |

**Skip if behind:** One sentence only; move to evidence.

---

### 2:10–2:40 | Act 6 — Evidence (Judge HTML provenance)

| | |
|--|--|
| **Screen** | Scroll to provenance + mention `make judge` (do NOT lead with metrics table) |
| **Objective** | Trust without overclaiming |
| **Talking point** | "Everything regenerates from code. SHA-256 manifest. We label synthetic metrics honestly — pipeline verification, not inflated production claims. We do not ask you to trust markdown." |
| **Expected reaction** | Trust increase — "they're careful" |

**If metrics visible:** "FG mIoU 0.20 on synthetic fixture — proves pipeline. Not our production claim."

---

### 2:40–3:00 | Act 7 — Close

| | |
|--|--|
| **Screen** | Return to Survey Intelligence card (full circle) |
| **Objective** | Memory anchor |
| **Talking point** | "We built a geospatial decision-support system for SVAMITVA: orthomosaic in, survey officer briefing out — with road access analysis, review zones, and field recommendations. Open `evidence/judge_package/index.html` — the briefing is at the top." |
| **Expected reaction** | Clear memory hook for scoring |

---

## Timing Discipline

| If… | Then… |
|-----|--------|
| Demo crashes at 0:30 | Switch to judge HTML tab 1 — intelligence card |
| Judge asks mIoU early | 20 sec `METRICS_DEFENSE.md` → pivot back to intelligence |
| Judge is GIS-focused | Extend Act 5 (+15 sec), cut Act 6 |
| Judge is ML-focused | Act 6 metrics honesty (+15 sec), still end on intelligence |

---

## Screens to NEVER Show First

1. Metrics table with FG mIoU 0.20
2. `docs/audit-archive/` anything
3. Training loss curves
4. Bridge class discussion (unless asked)
5. GitHub file tree

---

## Post-Demo Handoff

Give judge one line written on submission form or chat:

> **Open `evidence/judge_package/index.html` — survey briefing at top, `make judge` to verify.**

---

*Pair with `METRICS_DEFENSE.md`, `POSITIONING.md`, `JUDGE_QA_MASTER.md`.*
