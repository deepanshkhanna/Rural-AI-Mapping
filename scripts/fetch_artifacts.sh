#!/usr/bin/env bash
# Fetch production checkpoints and validation data (out-of-band release assets).
# Set SVAMITVA_ARTIFACTS_URL to a tarball or directory manifest before running.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

URL="${SVAMITVA_ARTIFACTS_URL:-}"

if [[ -z "$URL" ]]; then
  echo "SVAMITVA_ARTIFACTS_URL is not set."
  echo "For CI/local verification without release assets, run: bash scripts/reproduce.sh"
  echo ""
  echo "To use production artifacts, set SVAMITVA_ARTIFACTS_URL to a release tarball containing:"
  echo "  outputs/checkpoints/best_model.pth"
  echo "  outputs/checkpoints/latest_model.pth"
  echo "  outputs/optimal_bias.json"
  echo "  data/ (orthomosaics + shapefiles)"
  echo ""
  echo "To create a release tarball from local artifacts:"
  echo "  bash scripts/package_production_release.sh"
  exit 1
fi

mkdir -p outputs/checkpoints data
echo "Fetching artifacts from $URL ..."
curl -fsSL "$URL" -o /tmp/svamitva_artifacts.tar.gz
tar -xzf /tmp/svamitva_artifacts.tar.gz -C "$ROOT"
echo "Artifacts extracted. Run: python run_calibrated_eval.py --require-bias"
