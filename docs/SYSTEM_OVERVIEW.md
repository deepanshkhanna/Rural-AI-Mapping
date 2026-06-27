# System Overview

## What the System Does

This is an automated geospatial feature extraction system for the SVAMITVA scheme. It takes high-resolution drone orthomosaics (GeoTIFF format) as input and produces pixel-level segmentation masks for operational submission classes:

- **Road** (class 1) -- paved and unpaved village roads
- **Built-Up Area** (class 3) -- residential and commercial structures
- **Water Body** (class 4) -- lakes, ponds, and water channels

Bridge (class 2) is present in the model taxonomy but non-operational in this submission cycle.

## Key Metrics

| Metric | Value |
|--------|-------|
| Foreground mIoU | 0.3871 |
| Road IoU | 0.5555 |
| Built-Up IoU | 0.1615 |
| Water Body IoU | 0.8315 |
| Bridge IoU | 0.0000 |

## Metric Provenance

- Evaluator: `run_calibrated_eval.py` + unified count-based metric computation
- Checkpoint pipeline: `outputs/checkpoints/best_model.pth` (EMA epoch 43) + `outputs/checkpoints/latest_model.pth` (EMA epoch 80)
- Calibration status: Enabled (`outputs/optimal_bias.json`)
- TTA status: Enabled
- Postprocessing status: Enabled
- Date/source artifact: `outputs/calibrated_eval_results.json` (2026-06-07 00:37:33 +0530)

## Pipeline Stages

```
[TIFF + SHP] --> [Patch Extraction] --> [Training] --> [Best Checkpoint]
                                                              |
                                                              v
[Test TIFF] --> [Sliding Window] --> [Predicted GeoTIFF Mask + Visualization]
```

### Stage 1: Data Ingestion
- Reads large GeoTIFFs (up to 235K x 120K pixels) via windowed rasterio access
- Reprojects shapefile annotations to match each TIFF's CRS on-the-fly
- Rasterizes vector geometries to pixel masks per patch

### Stage 2: Training
- Extracts 768x768 patches with minority-aware centroid sampling
- Trains DeepLabV3+ with Focal + Dice loss for 80 epochs
- Maintains EMA shadow weights for robust checkpointing

### Stage 3: Inference
- Sliding-window inference with 512x512 patches and 64px overlap
- Strip-based processing to bound memory usage on large TIFFs
- Outputs georeferenced GeoTIFF masks with original CRS preserved

### Stage 4: Evaluation
- Patch-based validation on deterministic grid (512 patches)
- Official board-facing metrics from calibrated end-to-end evaluator
- Training curve visualization (2D + 3D plots)

## Entry Points

| Script | Purpose |
|--------|---------|
| `train.py` | Train the segmentation model |
| `test_inference.py` | Run inference on test TIFFs |
| `evaluate_model_statistics.py` | Generate evaluation report |
| `visualize_training.py` | Plot training curves |
| `src/inference/evaluate.py` | Standalone CLI evaluation |
| `src/inference/export_model.py` | Export checkpoint / ONNX |
