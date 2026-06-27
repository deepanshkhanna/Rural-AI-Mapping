# Demo Recovery — Presentation Ready

**Recovered from:** git stash `53577645` + dangling commit `282d8e57`

## Live demo (5 min)

```bash
cd /home/dk/ml_projects/iit_hackathon
bash scripts/start_demo_gpu.sh
```

1. Select **`04_fattu_bhila_building_heavy`**
2. **TTA OFF**
3. Run inference → Download GPKG
4. Say: *"Experimental roof_type_code integers 1–4 in building_footprints"*

## Certified metric

**FG mIoU 0.4809** — `production_release/metrics/epoch_71_results.json`

## Offline fallback

`judge_package/` — open GPKG + attribute table PNG if GPU fails

## Do NOT claim

RCC/Tin, 95% accuracy, production roof materials
