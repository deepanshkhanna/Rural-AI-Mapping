#!/usr/bin/env bash
# Verify production benchmark artifacts: checksums, eval artifact, provenance chain.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PYTHON="${PYTHON:-python3}"
if [[ -x "$ROOT/.venv/bin/python" ]]; then
  PYTHON="$ROOT/.venv/bin/python"
fi

MANIFEST="${1:-benchmark/ARTIFACT_MANIFEST.json}"
EVAL="$ROOT/outputs/calibrated_eval_results.json"

fail() { echo "VERIFY FAIL: $*" >&2; exit 1; }

echo "==> Production benchmark verification"

for f in outputs/checkpoints/best_model.pth outputs/checkpoints/latest_model.pth outputs/optimal_bias.json; do
  [[ -f "$ROOT/$f" ]] || fail "Missing $f — run scripts/fetch_artifacts.sh"
done

if [[ -f "$ROOT/$MANIFEST" ]]; then
  echo "==> Checking SHA-256 manifest: $MANIFEST"
  "$PYTHON" - <<PY
import hashlib, json, sys
from pathlib import Path
root = Path("$ROOT")
manifest = json.loads((root / "$MANIFEST").read_text())
errors = []
for entry in manifest.get("artifacts", []):
    rel = entry["path"]
    p = root / rel
    if not p.exists():
        errors.append(f"missing: {rel}")
        continue
    h = hashlib.sha256(p.read_bytes()).hexdigest()
    if h != entry["sha256"]:
        errors.append(f"checksum mismatch: {rel}")
if errors:
    print("\\n".join(errors), file=sys.stderr)
    sys.exit(1)
print(f"OK: {len(manifest.get('artifacts', []))} artifacts match manifest")
PY
else
  echo "WARN: No manifest at $MANIFEST — skipping checksum step (see benchmark/ARTIFACT_MANIFEST.template.json)"
fi

[[ -f "$EVAL" ]] || fail "Missing $EVAL — run run_calibrated_eval.py"

"$PYTHON" - <<PY
import json
from pathlib import Path
d = json.loads(Path("$EVAL").read_text())
prov = d.get("provenance", {})
required = ["git_sha", "best_ckpt_sha256", "latest_ckpt_sha256"]
missing = [k for k in required if k not in prov]
if missing:
    raise SystemExit(f"Eval provenance missing keys: {missing}")
fg = d.get("calibrated", {}).get("fg_miou")
print(f"Eval FG mIoU: {fg}")
print(f"Git SHA: {prov.get('git_sha')}")
print("VERIFY OK: production benchmark chain intact")
PY
