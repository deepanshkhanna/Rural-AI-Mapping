"""Pytest configuration and shared synthetic fixtures."""

from __future__ import annotations

import json
import subprocess
import sys
import os
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_SCRIPT = ROOT / "scripts" / "build_synthetic_fixtures.py"


@pytest.fixture(scope="session", autouse=True)
def ensure_synthetic_fixtures() -> None:
    """Build synthetic checkpoints/fixtures once per test session if missing."""
    os.environ.setdefault("SVAMITVA_CONFIG_PATH", "config/platform_config.synthetic.json")
    from src.config.platform_config import load_platform_config

    load_platform_config.cache_clear()

    ckpt = ROOT / "outputs" / "checkpoints" / "best_model.pth"
    if not ckpt.exists():
        subprocess.check_call([sys.executable, str(FIXTURE_SCRIPT)], cwd=ROOT)


@pytest.fixture
def synthetic_manifest() -> dict:
    path = ROOT / "tests" / "fixtures" / "synthetic" / "manifest.json"
    return json.loads(path.read_text(encoding="utf-8"))
