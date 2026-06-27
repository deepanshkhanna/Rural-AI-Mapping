#!/usr/bin/env bash
# One-command judge verification: fixtures → train → eval → evidence bundle → summary card.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PYTHON="${PYTHON:-python3}"
if [[ -x "$ROOT/.venv/bin/python" ]]; then
  PYTHON="$ROOT/.venv/bin/python"
fi

export SVAMITVA_CONFIG_PATH="${SVAMITVA_CONFIG_PATH:-config/platform_config.synthetic.json}"

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  SVAMITVA Judge Verification (synthetic benchmark path)    ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

echo "==> Step 1/3: Train demo model + regenerate evidence package"
"$PYTHON" scripts/generate_judge_package.py --train

PKG="$ROOT/evidence/judge_package"
EVAL="$ROOT/outputs/calibrated_eval_results.json"

echo ""
echo "==> Step 2/3: Verification summary"
if [[ -f "$PKG/metrics.json" ]]; then
  FG_MIOU="$("$PYTHON" -c "import json; d=json.load(open('$PKG/metrics.json')); print(f\"{d['patch_verification'].get('fg_miou', 0):.4f}\")")"
  echo "  Full-raster FG mIoU (synthetic): $FG_MIOU"
fi
if [[ -f "$PKG/verification_manifest.json" ]]; then
  SHA="$("$PYTHON" -c "import json; d=json.load(open('$PKG/verification_manifest.json')); print(d['provenance'].get('git_sha','?')[:12])")"
  echo "  Git SHA: $SHA"
  echo "  Manifest: evidence/judge_package/verification_manifest.json"
fi
if [[ -f "$EVAL" ]]; then
  echo "  Eval artifact: outputs/calibrated_eval_results.json"
fi

echo ""
echo "==> Step 3/3: Open evidence"
echo "  file://$PKG/index.html"
echo ""
echo "Optional production benchmark (requires release tarball):"
echo "  export SVAMITVA_ARTIFACTS_URL='<url>'"
echo "  bash scripts/fetch_artifacts.sh"
echo "  SVAMITVA_CONFIG_PATH=config/platform_config.v1.json python run_calibrated_eval.py --require-bias"
echo "  bash scripts/verify_production_benchmark.sh"
echo ""
echo "Judge verification complete."
