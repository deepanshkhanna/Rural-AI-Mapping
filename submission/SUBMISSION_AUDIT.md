# Submission Audit

**Status:** Frozen — submission mode  
**Certified release:** `v1.0-certified`  
**Audit date:** 2026-06-22

## Single Source of Truth

All submission claims derive from **`production_release/`** plus the evaluation entry point **`run_calibrated_eval.py`**.

| Artifact | Authoritative path |
|----------|-------------------|
| Checkpoints | `production_release/checkpoints/best_model.pth`, `latest_model.pth` |
| Calibration | `production_release/bias/optimal_bias.json` |
| Metrics | `production_release/metrics/epoch_71_results.json` |
| Integrity | `production_release/MANIFEST.json`, `production_release/checksums/SHA256SUMS.txt` |
| Config | `config/platform_config.v1.json` |
| Evaluation | `run_calibrated_eval.py` |
| Inference | `src/inference/calibrated_engine.py` |

## Best Checkpoint

**Winner: epoch_71 ensemble**

| Component | Detail |
|-----------|--------|
| `best_model.pth` | Epoch 71, weight **0.65** |
| `latest_model.pth` | Epoch 80 EMA, weight **0.35** |
| SHA-256 (best) | `8675e06ae0584bd5105b88f2e8356777d85d7eaeb585c4b4381a087162f7d892` |
| SHA-256 (latest) | `f8f45947be59825fbb6addc54c75d748f1722d57bb636299bfe9a1da51ca1aa7` |

## Best Metrics (Calibrated + TTA + Postprocess)

598 validation patches across NADALA + NAGUL.

| Metric | Value |
|--------|-------|
| **FG mIoU** | **0.4809** |
| Road IoU | 0.4356 |
| Built-Up IoU | 0.7415 |
| Water IoU | 0.7466 |
| Bridge IoU | 0.0000 |

Per-village stress (TTA): NADALA FG 0.5882, NAGUL FG 0.4124.

## Best Evaluation Report

`production_release/reports/FINAL_MODEL_RANKING.md` — ranks epoch_71 above epochs 33, 69, and 80 under identical protocol.

Supporting reports in `production_release/reports/`:
- `FINAL_MODEL_CERTIFICATION.md`
- `SVAMITVA_FINAL_PRODUCTION_DECISION.md`
- `WINNER_STRESS_REPORT.md`
- `PRODUCTION_RELEASE_MANIFEST.md`

## Calibration

Optimal per-class logit bias: **`[-0.5, 0.75, 0.0, -0.5, -0.5]`**

Classes: Background, Road, Bridge, Built-Up Area, Water Body.

Bias-search FG mIoU (patch-level, bias only): 0.5091.

## Final Inference Pipeline

```
Input patch / GeoTIFF
  → ImageNet normalization
  → Two-model ensemble (65% best + 35% latest EMA)
  → Per-class logit bias
  → TTA (horizontal + vertical flip averaging)
  → Postprocessing (road gap fill, bridge spatial recovery)
  → Class mask + statistics
```

Entry points:
- Evaluation: `run_calibrated_eval.py`
- Production API: `production/api.py` → `CalibratedEngine`
- Demo: `demo_ui/app.py`

## Final Architecture

| Parameter | Value |
|-----------|-------|
| Model | DeepLabV3Plus |
| Encoder | ResNet50 (ImageNet) |
| Parameters | 26,735,987 |
| Input size | 768×768 |
| Classes | 5 (Background + 4 foreground) |

Factory: `src/models/model_factory.py`  
Loss (training): `src/losses/multiclass_loss.py` (FocalTversky composite)

## Final Dataset Configuration

From `config/platform_config.v1.json`:

**Train (6 villages):**
- PINDORI MAYA SINGH-TUGALWAL_28456_ortho
- TIMMOWAL_37695_ORI
- BADETUMNAR_450157_BANGAPAL_450155_CHHOTETUMAR_450149_MOFALNAR_450150_ORTHO
- MURDANDA_450879_AWAPALLI_CHINTAKONTA_ORTHO
- KUTRU_451189_AAKLANKA_451163_ORTHO
- SAMLUR_450163_SIYANAR_450164_KUTULNAR_450165_BINJAM_450166_JHODIYAWADAM_450167_ORTHO

**Validation (2 villages):**
- 28996_NADALA_ORTHO
- NAGUL_450171_MADASE_450172_GHOTPAL_450137_ORTHO

Training: 150 patches/image, batch 4, accumulation 8, 80 epochs.

## Rejected Alternatives (Non-Authoritative)

Post-V1 experiments in `archive/experiment/` did not replace the certified model:

| Experiment | Verdict | Best FG vs V1 |
|------------|---------|---------------|
| exp04 SegFormer-B3 | Reject | 0.4038 |
| exp06 road precision | Paused | Did not beat V1 |
| exp07 road density sampler | Abandon | Gate failed |
| exp08 CG3-DBS | Reject | NAGUL FG 0.4199 |
| exp09 village expansion | Reject | Marathon regressed |

## Non-Authoritative Paths

Do not cite metrics from:
- `archive/` (research and superseded docs)
- `evidence/judge_package/` (synthetic verification demo)
- Legacy `docs/SYSTEM_OVERVIEW.md` (archived)
