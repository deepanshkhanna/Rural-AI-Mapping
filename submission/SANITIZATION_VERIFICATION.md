# Sanitization Verification

**Date:** 2026-06-27  
**Pass type:** Post-sanitization functional check

## Protected Artifacts — Verified Intact

| Artifact | Status |
|----------|--------|
| `production_release/checkpoints/best_model.pth` | ✅ Present (320,672,655 bytes) |
| `production_release/checkpoints/latest_model.pth` | ✅ Present (427,751,129 bytes) |
| `production_release/metrics/epoch_71_results.json` | ✅ Present (FG mIoU 0.4809 unchanged) |
| `production_release/MANIFEST.json` | ✅ Present (SHA-256 checksums unchanged) |
| `run_calibrated_eval.py` | ✅ Unmodified |
| `train.py` | ✅ Unmodified |
| `src/` core modules | ✅ Present |
| `demo_ui/` | ✅ Present |

## Checks Run

| Check | Result | Notes |
|-------|--------|-------|
| Core module imports | ✅ PASS | `src.export.vector_export`, `tiling`, `postprocessing`, `survey_report` |
| `vector_export.py` | ✅ RESTORED | Recovered from git `54f6dee` (was missing pre-pass) |
| pytest suite | ⚠️ PARTIAL | `tests/test_api.py` fails: `Router.__init__() got unexpected keyword argument 'on_startup'` (pre-existing FastAPI/Starlette mismatch) |
| `bias_search.py` import | ⚠️ FAIL | `albucore.utils.preserve_channel_dim` missing — env dependency issue |
| Demo startup | ⚠️ NOT RUN | Requires checkpoints + Streamlit; paths verified |
| Vector export | ✅ Module loads | CLI: `scripts/export_vectors.py` |
| Roof export | ⚠️ NOT RUN | `src/roof_material/` present; no smoke run |
| Evaluation script | ⚠️ Import blocked | Same albucore issue as bias_search |

## Functionality Assessment

**No submission metrics altered.** Checkpoints and epoch_71 JSON untouched.

**No certified submission artifacts deleted.** Experimental outputs only.

**Submission judge docs:** Restored from agent-transcript backup after accidental loss during intermediate cleanup — **verify content hash against team backup before final submit**.

## Risk Items

1. Submission files restored programmatically — human review recommended
2. Test suite not fully green (environment/API compatibility)
3. `docs/SYSTEM_OVERVIEW.md` contains outdated metrics (protected from edit)

## Rollback

Full manifest: `submission/ROLLBACK_MANIFEST_2026-06-27.txt`

## Verdict

**REQUIRES REVIEW** — Structure and artifacts are submission-ready; run full `make judge` + manual demo smoke test before final lock.
