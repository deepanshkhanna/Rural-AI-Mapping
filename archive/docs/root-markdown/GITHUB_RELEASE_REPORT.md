# GITHUB RELEASE REPORT

**Date:** 2026-06-16  
**Tag:** `v1.0-certified`  
**Title:** RailVigil / SVAMITVA Certified Stable V1

## Release Status

| Item | Local | Remote |
|------|-------|--------|
| Tag `v1.0-certified` | CREATED | Push after branch push |
| Branch `stable/v1` | CREATED | Push with main |
| Branch `experiment/main` | CREATED | Push with main |
| GitHub Release | PREPARED | Create after tag push |
| Recovery bundle asset | READY (`recovery_bundle_v1.zip`, 1.38 GB) | **Required** — checkpoints not in git |

**Note:** Model checkpoints (305–408 MB each) exceed GitHub's 100 MB file limit. They are **not** in the repository. Download `recovery_bundle_v1.zip` from this release and follow `CHECKPOINT_RECOVERY.md`.

## Release Notes (for GitHub)

### Certified Model

- **epoch_71 ensemble:** DeepLabV3Plus-ResNet50 (26,735,987 parameters)
- best@71 (weight 0.65) + latest@80 EMA (weight 0.35)
- Bias: `[-0.5, 0.75, 0.0, -0.5, -0.5]`
- Artifacts: `production_release/`

### Benchmark Metrics (calibrated + TTA + postprocess)

| Metric | Value |
|--------|-------|
| FG mIoU | **0.4809** |
| Road IoU | 0.4356 |
| Built-Up IoU | 0.7415 |
| Water IoU | 0.7466 |
| Bridge IoU | 0.0000 |

598 validation patches, NADALA + NAGUL.

### Reproducibility Status

**PASS** — metrics reproduced exactly from frozen `production_release/` artifacts. See `REPRODUCIBILITY_AUDIT.md` and `RECOVERY_VERIFICATION_REPORT.md`.

### Confidence Score

**0.82** (production certification)

### Known Limitations

1. Bridge class not detectable (IoU 0.0)
2. Large village-to-village variance (NADALA FG 0.5882 vs NAGUL FG 0.4124)
3. Patch-level validation ≠ full orthomosaic raster score
4. Train villages (6) disjoint from val villages (2)

### Recovery Instructions

```bash
git clone https://github.com/deepanshkhanna/iit_hackathon.git
cd iit_hackathon
git checkout v1.0-certified
pip install -r requirements.txt
cp production_release/checkpoints/*.pth outputs/checkpoints/
cp production_release/bias/optimal_bias.json outputs/optimal_bias.json
python run_calibrated_eval.py --require-bias
```

Alternatively, download `recovery_bundle_v1.zip` from this release and follow `REPRODUCIBILITY_GUIDE.md`.

## Commands to Complete Release

```bash
# 1. Push branches and tag (no large checkpoints in git)
git push -u origin main stable/v1 experiment/main
git push origin v1.0-certified

# 2. Create GitHub release — recovery bundle REQUIRED for checkpoints
gh release create v1.0-certified \
  --title "RailVigil / SVAMITVA Certified Stable V1" \
  --notes-file GITHUB_RELEASE_REPORT.md \
  recovery_bundle_v1.zip
```

## Documentation Links

- [MODEL_CARD.md](MODEL_CARD.md)
- [BENCHMARK_CARD.md](BENCHMARK_CARD.md)
- [DATASET_CARD.md](DATASET_CARD.md)
- [SVAMITVA_SUBMISSION_CERTIFICATION.md](SVAMITVA_SUBMISSION_CERTIFICATION.md)
- [BASELINE_SNAPSHOT.md](BASELINE_SNAPSHOT.md)
- [BRANCH_STRATEGY.md](BRANCH_STRATEGY.md)
