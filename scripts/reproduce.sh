#!/usr/bin/env bash
# Reproduce evaluation pipeline end-to-end (synthetic fixtures for CI; real artifacts for production).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PYTHON="${PYTHON:-python3}"
if [[ -x "$ROOT/.venv/bin/python" ]]; then
  PYTHON="$ROOT/.venv/bin/python"
fi

echo "==> Building synthetic geodata fixtures"
if [ -f outputs/checkpoints/best_model.pth ]; then
  "$PYTHON" scripts/build_synthetic_fixtures.py --skip-checkpoints
else
  "$PYTHON" scripts/build_synthetic_fixtures.py
fi

export SVAMITVA_CONFIG_PATH="${SVAMITVA_CONFIG_PATH:-config/platform_config.synthetic.json}"

echo "==> Running calibrated evaluation (config: $SVAMITVA_CONFIG_PATH)"
"$PYTHON" run_calibrated_eval.py --require-bias

echo "==> Reproduce complete. Results: outputs/calibrated_eval_results.json"
