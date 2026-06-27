# Repository Review

**Date:** 2026-06-27  
**Reviewer friendliness:** **8.5 / 10**

## Structure (after sanitization)

```
README.md                 ← Single root entry
docs/                     ← Architecture, training, evaluation
config/                   ← Locked platform config
src/                      ← Core library + export
train.py                  ← Training
run_calibrated_eval.py      ← Official metrics
production_release/       ← Frozen v1.0-certified artifacts
production/               ← FastAPI
demo_ui/                  ← Streamlit demo
evidence/judge_package/   ← HTML verification bundle
submission/               ← Lock, audit, judge prep + sanitization reports
scripts/                  ← reproduce, judge, export, install checkpoints
archive/                  ← Superseded research (do not cite)
```

## Install Path

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## Reproduction Path

```bash
make reproduce          # synthetic fixtures + eval
# OR production metrics:
bash scripts/install_production_checkpoints.sh
SVAMITVA_CONFIG_PATH=config/platform_config.v1.json python run_calibrated_eval.py --require-bias
```

## Demo Path

```bash
bash scripts/install_production_checkpoints.sh
streamlit run demo_ui/app.py
```

## GIS Export Path

```bash
python scripts/export_vectors.py --tiff demo_dataset/tiffs/06_nadala_validation_nadala.tif --output outputs/vectors/nadala.gpkg
```

## `.gitignore`

Adequate: blocks `data/`, `outputs/**` (with eval JSON exception), checkpoints, secrets, IDE files.

**Gap:** `.git-msg-filter.py` pattern not needed (file removed).

## Friction Points (−1.5)

1. Checkpoints not in git — requires `install_production_checkpoints.sh` or manual copy from `production_release/`
2. `docs/audit-archive/` still contains 45 historical audit files (noise for judges)
3. Pre-existing test/env issues (FastAPI Router API, albucore import) — see `SANITIZATION_VERIFICATION.md`

## Strengths (+)

- Clear certified metrics in README
- `make judge` one-command verification
- `submission/SUBMISSION_LOCK.md` + `production_release/MANIFEST.json` integrity chain
- Clean root after markdown reduction
