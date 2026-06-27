# Release Freeze Checklist

A release candidate (`v1.0.0-rc2`) may be **frozen** only when every item below is **GREEN**.

**Sign-off:** Technical Lead + one independent verifier (fresh clone).

**Freeze target:** Day 3, 12:00.

---

## 1. Tests Pass

```bash
cd <repo-root>
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && pip install -e ".[dev]"
export SVAMITVA_CONFIG_PATH=config/platform_config.synthetic.json
pytest --cov=src --cov=production --cov-fail-under=40
```

**Pass criteria:**
- [ ] Exit code 0
- [ ] ≥35 tests passed, 0 failed
- [ ] Coverage ≥40%

---

## 2. Judge Package Generates

```bash
export SVAMITVA_CONFIG_PATH=config/platform_config.synthetic.json
make judge
```

**Pass criteria:**
- [ ] Exit code 0
- [ ] `evidence/judge_package/index.html` exists and opens in browser
- [ ] `evidence/judge_package/metrics.json` contains `fg_miou` > 0.15
- [ ] `evidence/judge_package/verification_manifest.json` lists all files with SHA-256
- [ ] `evidence/judge_package/overlays/01_input_rgb.png` through `06_error_map.png` exist

**Fast path (pre-generated evidence acceptable at freeze if regenerated within 24h):**

```bash
test -f evidence/judge_package/index.html && test -f evidence/judge_package/metrics.json
```

---

## 3. Demo Works

```bash
# Requires checkpoints in outputs/checkpoints/
export SVAMITVA_CONFIG_PATH=config/platform_config.synthetic.json
streamlit run demo_ui/app.py --server.headless true &
sleep 8
curl -sf http://localhost:8501/_stcore/health
kill %1 2>/dev/null || true
```

**Pass criteria:**
- [ ] Streamlit starts without import errors
- [ ] Health endpoint returns 200
- [ ] **Judge Verification** page loads (`demo_ui/pages/2_Judge_Verification.py`)
- [ ] Inference on bundled synthetic sample produces non-empty mask (manual spot-check)

**Production demo path (required if benchmark tarball shipped):**

```bash
export SVAMITVA_ARTIFACTS_URL="<production-tarball-url>"
bash scripts/fetch_artifacts.sh
streamlit run demo_ui/app.py
```

- [ ] Demo runs with fetched production checkpoints

---

## 4. Benchmark Scripts Execute

### Synthetic reproducibility

```bash
export SVAMITVA_CONFIG_PATH=config/platform_config.synthetic.json
bash scripts/reproduce.sh
test -f outputs/calibrated_eval_results.json
```

**Pass criteria:**
- [ ] `outputs/calibrated_eval_results.json` contains `provenance.git_sha`
- [ ] `calibrated.fg_miou` or equivalent field present and > 0

### Production verification (required if tarball hosted)

```bash
export SVAMITVA_ARTIFACTS_URL="<production-tarball-url>"
bash scripts/fetch_artifacts.sh
SVAMITVA_CONFIG_PATH=config/platform_config.v1.json python run_calibrated_eval.py --require-bias
bash scripts/verify_production_benchmark.sh benchmark/ARTIFACT_MANIFEST.json
```

**Pass criteria:**
- [ ] `verify_production_benchmark.sh` prints `VERIFY OK`
- [ ] Production FG mIoU documented in eval JSON

### Package script (release manager)

```bash
bash scripts/package_production_release.sh
test -f benchmark/svamitva_production_benchmark.tar.gz
test -f benchmark/ARTIFACT_MANIFEST.json
```

- [ ] Tarball and manifest generated (run once before upload)

---

## 5. Documentation Accurate

Manual review — all must be true:

- [ ] README `SVAMITVA_ARTIFACTS_URL` is set or explicitly marked TBD with contact
- [ ] No headline mIoU cited only from markdown (must trace to `calibrated_eval_results.json` or judge `metrics.json`)
- [ ] Bridge marked non-operational in README
- [ ] Synthetic vs production metrics clearly labeled in `JUDGE_EXPERIENCE.md` and judge HTML
- [ ] `official_metrics_for_submission.md` matches artifact structure
- [ ] Archived metrics in `docs/audit-archive/` not referenced as current

---

## 6. Reproducibility Path Works (Fresh Clone)

On a machine **without** prior `.venv` or `outputs/checkpoints`:

```bash
git clone <repo-url> && cd <repo>
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
make judge
```

**Pass criteria:**
- [ ] Completes without manual intervention
- [ ] Judge HTML openable at `evidence/judge_package/index.html`

---

## 7. API & Docker (Secondary — Yellow if skipped)

```bash
docker build -t svamitva-api:rc .
pytest tests/test_api.py -q
```

- [ ] Docker image builds
- [ ] API tests pass

---

## 8. CI Parity

```bash
# Mirror .github/workflows/ci.yml locally or verify last GitHub Actions run
```

- [ ] Last CI run on `main`/`release/stable` is green

---

## Freeze Sign-Off

| Check | Verifier | Date | ✓ |
|-------|----------|------|---|
| Tests (§1) | | | |
| Judge package (§2) | | | |
| Demo (§3) | | | |
| Benchmark scripts (§4) | | | |
| Documentation (§5) | | | |
| Fresh clone (§6) | | | |
| API/Docker (§7) | | | |
| CI (§8) | | | |

**Frozen tag:** `v1.0.0-rc2`  
**Frozen commit:** `________________`  
**Technical Lead approval:** ________________

---

## Post-Freeze Allowed Changes

| Allowed | Not allowed |
|---------|-------------|
| P0 bug fixes | Features |
| Typo/doc fixes | Refactoring |
| Manifest URL updates | Dependency major bumps |
| Regenerated judge package (same code) | API changes |

Every post-freeze change requires: pytest green + `make judge` green + tag bump (`rc3`, `rc4`, …).
