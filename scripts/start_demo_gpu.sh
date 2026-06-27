#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export LD_LIBRARY_PATH="/usr/lib/wsl/lib:${LD_LIBRARY_PATH:-}"
export SVAMITVA_INFERENCE_DEVICE="${SVAMITVA_INFERENCE_DEVICE:-cuda}"
cd "$ROOT"
if ! nvidia-smi >/dev/null 2>&1; then
  echo "GPU not visible. Run 'wsl --shutdown' from Windows, reopen WSL, retry."
  exit 1
fi
exec .venv/bin/streamlit run demo_ui/app.py --server.headless true
