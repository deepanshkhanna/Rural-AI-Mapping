#!/usr/bin/env python3
"""
Export GIS vectors (GeoPackage) from a GeoTIFF orthomosaic using the certified pipeline.

Usage:
    python scripts/export_vectors.py --tiff path/to/ortho.tif --output outputs/vectors/village.gpkg

Requires checkpoints in outputs/checkpoints/ (see scripts/install_production_checkpoints.sh).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> int:
    parser = argparse.ArgumentParser(description="SVAMITVA mask → GeoPackage vector export")
    parser.add_argument("--tiff", required=True, type=Path, help="Input GeoTIFF orthomosaic")
    parser.add_argument("--output", required=True, type=Path, help="Output .gpkg path")
    parser.add_argument("--best-ckpt", type=Path, default=ROOT / "outputs/checkpoints/best_model.pth")
    parser.add_argument("--latest-ckpt", type=Path, default=ROOT / "outputs/checkpoints/latest_model.pth")
    parser.add_argument("--bias", type=Path, default=ROOT / "outputs/optimal_bias.json")
    parser.add_argument("--no-rooftop-heuristic", action="store_true", help="Polygonize full built-up mask")
    parser.add_argument("--roof-classifier", type=Path, default=None)
    parser.add_argument("--device", default=None, help="cuda or cpu (auto if omitted)")
    args = parser.parse_args()

    if not args.tiff.exists():
        print(f"ERROR: TIFF not found: {args.tiff}", file=sys.stderr)
        return 1
    for ckpt in (args.best_ckpt, args.latest_ckpt):
        if not ckpt.exists():
            print(f"ERROR: Checkpoint not found: {ckpt}", file=sys.stderr)
            print("Run: bash scripts/install_production_checkpoints.sh", file=sys.stderr)
            return 1

    import torch

    from src.export.vector_export import mask_to_geopackage
    from src.inference.calibrated_engine import CalibratedEngine

    device = args.device or ("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")
    print(f"Input:  {args.tiff}")
    print(f"Output: {args.output}")

    engine = CalibratedEngine.from_checkpoints(
        args.best_ckpt,
        args.latest_ckpt,
        device=device,
        bias_path=args.bias if args.bias.exists() else None,
    )

    from src.roof_material.classifier import RoofMaterialClassifier
    from src.roof_material.flags import ROOF_CLASSIFIER_ENABLED

    roof_classifier = None
    if ROOF_CLASSIFIER_ENABLED:
        roof_ckpt = args.roof_classifier or (ROOT / "checkpoints/roof_material/best.pt")
        if roof_ckpt.exists():
            roof_classifier = RoofMaterialClassifier(roof_ckpt, device=device)
            print(f"Roof classifier: {roof_ckpt}")

    mask, meta = engine.predict_tiff(args.tiff, output_path=None, postprocess=True)
    counts = mask_to_geopackage(
        mask, meta, args.output,
        building_use_rooftop_heuristic=not args.no_rooftop_heuristic,
        ortho_path=args.tiff,
        roof_classifier=roof_classifier,
    )

    print("Exported layers:")
    for layer, n in counts.items():
        print(f"  {layer}: {n} feature(s)")
    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
