# Judge Objection Database

Prepared responses to predictable "why not X?" challenges. Answer confidently with measured evidence.

---

## Why not Segment Anything Model (SAM)?

**Answer:** SAM is a prompt-based generalist segmenter, not trained on SVAMITVA's 5-class schema. It requires point/box prompts per object — impractical for village-wide orthomosaic processing. Zero-shot SAM on remote sensing underperforms supervised domain-specific models on structured classes like roads and water bodies. We need georeferenced multi-class masks at scale, not interactive instance segmentation.

**Evidence:** Supervised DeepLab FG 0.4809 vs zero-shot approaches that lack calibrated multi-class output. SAM has no built-in Road/Built-Up/Water taxonomy.

**If pressed:** "SAM is excellent for interactive editing of our output masks — as a post-processing tool, not a replacement."

---

## Why not YOLO?

**Answer:** YOLO is object detection (bounding boxes), not semantic segmentation. SVAMITVA needs pixel-accurate masks that cover entire road networks, settlement areas, and water bodies — not bounding boxes around individual objects. Roads are linear features spanning the full image; YOLO's box paradigm loses topology and connectivity. Semantic segmentation is the correct formulation.

**Evidence:** Shapefile labels are polygon masks rasterized to pixels. Evaluation uses per-class IoU, not mAP.

**If pressed:** "YOLO could detect discrete structures (individual buildings) as a complementary module — but roads and water require dense segmentation."

---

## Why not Transformers (SegFormer, ViT)?

**Answer:** We tested SegFormer-B3 under identical data, loss, and eval protocol. Calibrated FG mIoU: **0.4038** vs our DeepLab **0.4809** — a 7.7-point gap. With only 6 training villages and extreme class imbalance, CNN inductive bias and ImageNet pretraining were more data-efficient. Transformers need larger datasets to outperform CNNs on remote sensing.

**Evidence:** `archive/experiment/exp04_segformer_b3/SEGFORMER_FINAL_VERDICT.md` — REJECT, guardian would have stopped at epoch 10.

---

## Why only DeepLab?

**Answer:** We are not "only DeepLab" — our submission is a **pipeline**: ensemble + calibration + TTA + postprocessing + survey intelligence. DeepLabV3Plus is the backbone that won our measured comparison. We certified 4 epoch candidates and tested SegFormer. The architecture is one component of a system that includes geospatial validation, postprocessing, and deployment infrastructure.

**Evidence:** FINAL_MODEL_RANKING.md (4 candidates); inference pipeline in calibrated_engine.py.

---

## Why is Road weaker than Built-Up and Water?

**Answer:** Three structural reasons: (1) Roads are 1–2 pixels wide at 0.3 m GSD — near the resolution limit. (2) Extreme class imbalance — roads are <1% of pixels. (3) High visual confusion with bare soil, paths, and shadows. Road IoU 0.4356 but **recall 0.6423** — we find most roads; boundary precision is the challenge. Built-Up and Water are areal features with stronger visual signatures.

**Evidence:** Road gt_pixels 6.2M vs visual width; Road recall 0.64 vs Built-Up 0.87 in epoch_71_results.json.

---

## Why not more training data?

**Answer:** We used all competition villages provided (6 train, 2 val). We tested adding 2 more villages (exp09) — marathon training to 86 epochs caused validation regression (FG 0.5077 at ep67 → 0.4493 at ep86). More data helps only with **diversity**, not just count. Our roadmap prioritizes stratified village acquisition across terrains, especially NAGUL-like hard cases.

**Evidence:** exp09 marathon report — REJECT. NAGUL FG 0.4124 demonstrates need for terrain diversity.

---

## Why not LiDAR?

**Answer:** LiDAR/DSM would help disambiguate roads from paths and roofs from bare ground — we scoped this as exp01 (DSM multimodal). It was not executed because RGB orthomosaics are available for all SVAMITVA villages; elevation data is not. We built the RGB pipeline first as the universal baseline. DSM fusion is our top multimodal roadmap item.

**Evidence:** `archive/experiment/exp01_dsm_multimodal/` scaffold exists. RGB-only ensures nationwide deployability.

---

## Why not foundation models (CLIP, SAM-2, GeoFM)?

**Answer:** Foundation models need fine-tuning or sophisticated prompting for domain-specific classes. With 6 training villages, fine-tuning a large foundation model risks overfitting with high compute cost. Our measured approach: supervised DeepLab with 27M params trains efficiently on limited data and produces calibrated, reproducible outputs. Foundation models are a 3-month roadmap item when more data is available.

**Evidence:** SegFormer (transformer family) underperformed with same data. Parameter/compute efficiency matters for government deployment.

---

## Why not self-training / pseudo-labeling?

**Answer:** Self-training amplifies model errors on unseen domains. With NAGUL already at FG 0.4124, pseudo-labeling on hard villages would reinforce mistakes without human verification. We use human-in-the-loop review zones instead of blind self-training. Active learning on low-confidence regions (with human correction) is safer for government deployment.

**Evidence:** NAGUL domain shift; explainability module flags uncertain regions for human review.

---

## Why did SegFormer fail?

**Answer:** SegFormer-B3 (mit_b3 encoder) achieved FG mIoU 0.4038 after 20 epochs with calibrated eval — 7.7 points below V1. Road IoU dropped 9.7 points (0.3384 vs 0.4356). Training was stable (no NaN, val loss decreased) but performance plateaued below gates. With 6 villages, the transformer could not leverage its capacity advantage. Guardian post-hoc verdict: STOP at epoch 10.

**Evidence:** SEGFORMER_FINAL_VERDICT.md — full metric table and gate analysis.

---

## Why did later epochs degrade?

**Answer:** Two cases: (1) **V1 training:** epoch 80 alone scores FG 0.4627 vs epoch 71's 0.4809 — mild overfitting after peak validation performance. That is why we ensemble ep71 (peak) with ep80 EMA (smoothed). (2) **exp09 marathon:** raw val FG peaked at epoch 67 (0.5077) then regressed to 0.4493 by epoch 86 — clear overfitting on expanded training set. Plateau governor correctly stopped training.

**Evidence:** FINAL_MODEL_RANKING.md (ep71 > ep80); exp09 marathon report (ep67 peak, ep86 regression).

---

## Why trust epoch 71?

**Answer:** Epoch 71 was selected through a **certification matrix** — not training loss, not a single run. Four candidates (epochs 33, 69, 71, 80) were evaluated with identical protocol: same 598 val patches, same bias search, same TTA, same postprocessing. Epoch 71 wins on FG mIoU (0.4809) and Water IoU (0.7466). Checkpoint SHA-256 is checksummed in MANIFEST.json. Fully reproducible.

**Evidence:** FINAL_MODEL_RANKING.md ranking table; SHA `8675e06a…` for best_model.pth.

---

## Quick Reference Card (Print This)

| Objection | One-Line Response |
|-----------|-------------------|
| SAM | "Prompt-based, not multi-class geospatial segmentation" |
| YOLO | "Detection ≠ segmentation; we need pixel masks" |
| Transformers | "SegFormer tested: 0.40 vs our 0.48" |
| More data | "exp09 added data, model regressed" |
| LiDAR | "Not available nationwide; RGB first" |
| Foundation models | "Need more data; SegFormer already failed" |
| Self-training | "Amplifies errors on hard villages" |
| Later epochs | "Certified matrix; ep71 beats ep80" |
| Road weak | "1–2 px wide, 0.64 recall, precision is hard" |
| Trust results | "Reproduce: `run_calibrated_eval.py --require-bias`" |
