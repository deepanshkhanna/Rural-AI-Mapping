# Submission Lock

**Effective:** 2026-06-22  
**Release tag:** `v1.0-certified`  
**Winner:** epoch_71 ensemble

This document is the frozen configuration contract. Any path, metric, or parameter not listed here is **non-authoritative**.

---

## Architecture

| Field | Locked value |
|-------|--------------|
| Segmentation head | DeepLabV3Plus |
| Encoder | `resnet50` |
| Pretrained weights | ImageNet |
| Input resolution | 768 px |
| Output classes | 5 |
| Parameters | 26,735,987 |

Source: `config/platform_config.v1.json`, `src/models/model_factory.py`

---

## Dataset Split

| Split | Villages | Count |
|-------|----------|-------|
| Train | See `platform_config.v1.json` → `splits.train_tiffs` | 6 |
| Val | `28996_NADALA_ORTHO`, `NAGUL_450171_MADASE_450172_GHOTPAL_450137_ORTHO` | 2 |

Val patches for scoring: **598**  
CRS allowlist: EPSG 32643, 32644, 3857

---

## Training Parameters

| Parameter | Value |
|-----------|-------|
| Patches per image | 150 |
| Batch size | 4 |
| Gradient accumulation | 8 |
| Epochs | 80 |
| Best checkpoint epoch | 71 |
| Latest (EMA) epoch | 80 |
| Loss | FocalTversky composite v1 |

Training entry: `train.py` with `SVAMITVA_CONFIG_PATH=config/platform_config.v1.json`

---

## Inference Parameters

| Parameter | Value |
|-----------|-------|
| Ensemble weights | best **0.65**, latest **0.35** |
| TTA | Enabled (H-flip + V-flip averaging) |
| Tile size | 768 |
| Eval batch size | 8 |
| Eval workers | 4 |

Engine: `src/inference/calibrated_engine.py`

---

## Bias Calibration

File: `production_release/bias/optimal_bias.json`

```json
[-0.5, 0.75, 0.0, -0.5, -0.5]
```

Mapping: `[Background, Road, Bridge, Built-Up Area, Water Body]`

Bias search entry: `bias_search.py`

---

## TTA

- Horizontal flip: logits averaged with original
- Vertical flip: logits averaged with original
- Applied before argmax and postprocessing

Controlled by `CalibratedEngine(use_tta=True)` — default in production eval.

---

## Postprocessing

Applied in order (`src/postprocessing.py`):

1. Road gap fill
2. Bridge spatial recovery from built-up context
3. Rooftop classification refinement

Eval reports **calibrated + postprocess** numbers as the submission metric.

---

## Checkpoint SHA-256

| File | SHA-256 |
|------|---------|
| `production_release/checkpoints/best_model.pth` | `8675e06ae0584bd5105b88f2e8356777d85d7eaeb585c4b4381a087162f7d892` |
| `production_release/checkpoints/latest_model.pth` | `f8f45947be59825fbb6addc54c75d748f1722d57bb636299bfe9a1da51ca1aa7` |
| `production_release/bias/optimal_bias.json` | `4ff3321bb6aa06c46e834f844ea0e3a1b574e806bd0515c4531b71e51d0e788e` |

Verify:

```bash
cd production_release/checksums && sha256sum -c SHA256SUMS.txt
```

Recovery bundle: `production_release/recovery_bundle_v1.zip` (offline distribution).

---

## Locked Metrics

Protocol: 598 val patches, NADALA + NAGUL, ensemble + bias + TTA + postprocess.

| Metric | Value |
|--------|-------|
| **FG mIoU** | **0.4809** |
| Road IoU | 0.4356 |
| Built-Up IoU | 0.7415 |
| Water IoU | 0.7466 |
| Bridge IoU | 0.0000 |

Canonical record: `production_release/metrics/epoch_71_results.json`

---

## Reproduction Command

```bash
# Link or copy frozen artifacts
mkdir -p outputs/checkpoints
cp production_release/checkpoints/*.pth outputs/checkpoints/
cp production_release/bias/optimal_bias.json outputs/optimal_bias.json

# Run locked eval
SVAMITVA_CONFIG_PATH=config/platform_config.v1.json \
  python run_calibrated_eval.py --require-bias
```

Expected FG mIoU: **0.4809** (requires `data/` orthomosaics and shapefiles).

---

## Non-Authoritative

Everything under `archive/`, experimental branches, and any metric not regenerated from the commands above.
