"""GIS certification for output GeoTIFF alignment and metadata integrity."""

from __future__ import annotations

import json
from pathlib import Path

import rasterio


TEST_DIR = Path("Test/live-demo")
PRED_DIR = Path("outputs/test_predictions_live_demo")
OUT_DIR = Path("outputs/recovery_reports")


def find_source_for_prediction(pred_name: str) -> Path | None:
    stem = pred_name.replace("_pred_mask", "")
    matches = list(TEST_DIR.rglob(f"{stem}.tif"))
    if matches:
        return matches[0]
    return None


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = []

    for pred in sorted(PRED_DIR.glob("*_pred_mask.tif")):
        src = find_source_for_prediction(pred.stem)
        if src is None:
            rows.append({"pred": str(pred), "status": "FAIL", "reason": "source_not_found"})
            continue

        with rasterio.open(src) as s, rasterio.open(pred) as p:
            crs_ok = str(s.crs) == str(p.crs)
            transform_ok = tuple(s.transform) == tuple(p.transform)
            shape_ok = (s.height == p.height and s.width == p.width)

            pixel_alignment_score = 1.0 if (transform_ok and shape_ok) else 0.0
            geom_alignment_score = 1.0 if (crs_ok and transform_ok) else 0.0

            rows.append(
                {
                    "source": str(src),
                    "prediction": str(pred),
                    "crs": str(p.crs),
                    "transform": [float(x) for x in tuple(p.transform)[:6]],
                    "crs_match": crs_ok,
                    "transform_match": transform_ok,
                    "shape_match": shape_ok,
                    "pixel_alignment_score": pixel_alignment_score,
                    "geometry_alignment_score": geom_alignment_score,
                    "status": "PASS" if (crs_ok and transform_ok and shape_ok) else "FAIL",
                }
            )

    status = "PASS" if rows and all(r.get("status") == "PASS" for r in rows) else "FAIL"
    out = {"status": status, "files": rows}
    (OUT_DIR / "gis_certification_report.json").write_text(json.dumps(out, indent=2), encoding="utf-8")

    lines = ["# GIS Certification Report", f"- Status: {status}", "", "## File Results"]
    for r in rows:
        lines.append(f"- prediction: {r.get('prediction', r.get('pred'))}")
        if r.get("status") == "FAIL" and "reason" in r:
            lines.append(f"  status: FAIL | reason: {r['reason']}")
            continue
        lines.append(f"  CRS: {r['crs']} | match={r['crs_match']}")
        lines.append(f"  Transform match: {r['transform_match']}")
        lines.append(f"  Pixel Alignment Score: {r['pixel_alignment_score']:.2f}")
        lines.append(f"  Geometry Alignment Score: {r['geometry_alignment_score']:.2f}")
        lines.append(f"  Status: {r['status']}")

    (OUT_DIR / "gis_certification_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUT_DIR / 'gis_certification_report.md'}")
    return 0 if status == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
