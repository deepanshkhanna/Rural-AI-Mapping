# Checkpoint Recovery (V1)

GitHub rejects model checkpoints over 100 MB. **Checkpoints are not stored in git.**

They are distributed via the **`v1.0-certified` GitHub release** asset `recovery_bundle_v1.zip`.

## Verified hashes (epoch_71 ensemble)

| File | SHA-256 |
|------|---------|
| `best_model.pth` (epoch 71) | `8675e06ae0584bd5105b88f2e8356777d85d7eaeb585c4b4381a087162f7d892` |
| `latest_model.pth` (epoch 80 EMA) | `f8f45947be59825fbb6addc54c75d748f1722d57bb636299bfe9a1da51ca1aa7` |
| `optimal_bias.json` | `4ff3321bb6aa06c46e834f844ea0e3a1b574e806bd0515c4531b71e51d0e788e` |

Bias is in git at `production_release/bias/optimal_bias.json`. Checkpoints must be downloaded from the release bundle.

## Option A — Full recovery bundle

```bash
# From GitHub release v1.0-certified, download recovery_bundle_v1.zip
unzip recovery_bundle_v1.zip
cp recovery_bundle/production_release/checkpoints/*.pth production_release/checkpoints/
cp recovery_bundle/production_release/checkpoints/*.pth outputs/checkpoints/
cp production_release/bias/optimal_bias.json outputs/optimal_bias.json
```

## Option B — Already have bundle at repo root

```bash
unzip -o recovery_bundle_v1.zip 'recovery_bundle/production_release/checkpoints/*' -d .
mv recovery_bundle/production_release/checkpoints/*.pth production_release/checkpoints/
mkdir -p outputs/checkpoints
cp production_release/checkpoints/*.pth outputs/checkpoints/
cp production_release/bias/optimal_bias.json outputs/optimal_bias.json
```

## Option C — Build locally (if you trained)

If `outputs/checkpoints/` still exists from training:

```bash
cp outputs/checkpoints/best_model.pth production_release/checkpoints/
cp outputs/checkpoints/latest_model.pth production_release/checkpoints/
sha256sum production_release/checkpoints/*.pth
# Must match hashes above
```

## Verify after restore

```bash
python run_calibrated_eval.py --require-bias --skip-validation
# Expected FG mIoU: 0.4809
```

See `production_release/checksums/SHA256SUMS.txt` for full artifact verification.
