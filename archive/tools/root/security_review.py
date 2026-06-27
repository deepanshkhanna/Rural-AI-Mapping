"""Basic automated security review checks."""

from __future__ import annotations

import json
import re
from pathlib import Path


RULES = [
    {
        "id": "unsafe_torch_load",
        "pattern": re.compile(r"torch\.load\(.*weights_only=False", re.IGNORECASE),
        "severity": "high",
        "description": "Unsafe checkpoint deserialization (weights_only=False)",
    },
    {
        "id": "dangerous_exec",
        "pattern": re.compile(r"(?<!\.)\b(eval|exec)\(", re.IGNORECASE),
        "severity": "critical",
        "description": "Dynamic code execution primitive",
    },
]

ALLOWLIST = {
    "src/security/checkpoints.py": {"unsafe_torch_load"},
}


def scan_repo(root: Path) -> list[dict]:
    findings = []
    for path in root.rglob("*.py"):
        if any(part in {".venv", "venv", "__pycache__"} for part in path.parts):
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for rule in RULES:
            for match in rule["pattern"].finditer(text):
                line = text.count("\n", 0, match.start()) + 1
                rel = str(path.relative_to(root))
                if rule["id"] in ALLOWLIST.get(rel, set()):
                    continue
                findings.append(
                    {
                        "rule": rule["id"],
                        "severity": rule["severity"],
                        "description": rule["description"],
                        "file": rel,
                        "line": line,
                    }
                )
    return findings


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    findings = scan_repo(root)

    out_dir = root / "outputs" / "recovery_reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_json = out_dir / "security_review_report.json"
    out_md = out_dir / "security_review_report.md"

    payload = {
        "status": "PASS" if not findings else "FAIL",
        "finding_count": len(findings),
        "findings": findings,
    }
    out_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    lines = [
        "# Security Review Report",
        f"- Status: {payload['status']}",
        f"- Findings: {payload['finding_count']}",
        "",
        "## Findings",
    ]
    if not findings:
        lines.append("- None")
    else:
        for f in findings:
            lines.append(
                f"- [{f['severity'].upper()}] {f['rule']} | {f['file']}:{f['line']} | {f['description']}"
            )
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {out_json}")
    print(f"Wrote {out_md}")
    return 0 if not findings else 3


if __name__ == "__main__":
    raise SystemExit(main())
