"""Demo certification checks for required UX and safety capabilities."""

from __future__ import annotations

import json
from pathlib import Path

OUT_DIR = Path("outputs/recovery_reports")
APP_PATH = Path("demo_ui/app.py")


REQUIRED_TOKENS = {
    "drag_and_drop_tiff": "st.file_uploader",
    "progress_or_loading": "st.spinner",
    "inference_timing": "elapsed",
    "confidence_map": "confidence",
    "class_statistics": "Class Distribution",
    "downloadable_outputs": "st.download_button",
    "error_handling": "st.error",
}


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    text = APP_PATH.read_text(encoding="utf-8")

    checks = {k: (v in text) for k, v in REQUIRED_TOKENS.items()}
    status = "PASS" if all(checks.values()) else "FAIL"

    out = {"status": status, "checks": checks}
    (OUT_DIR / "demo_certification_report.json").write_text(json.dumps(out, indent=2), encoding="utf-8")

    lines = ["# Demo Certification Report", f"- Status: {status}", "", "## Checks"]
    for k, ok in checks.items():
        lines.append(f"- {k}: {'PASS' if ok else 'FAIL'}")

    (OUT_DIR / "demo_certification_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUT_DIR / 'demo_certification_report.md'}")
    return 0 if status == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
