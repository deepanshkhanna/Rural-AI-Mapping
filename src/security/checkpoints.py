"""Security-focused checkpoint loading utilities."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import torch

from src.config.platform_config import load_platform_config


def file_sha256(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def load_checkpoint_secure(
    checkpoint_path: str | Path,
    map_location: Any = "cpu",
    expected_sha256: str | None = None,
) -> dict:
    """Load checkpoint with strict safe deserialization policy.

    This function always enforces ``weights_only=True`` and never performs
    unsafe pickle-based fallback loading.
    """
    _ = load_platform_config()

    ckpt_path = Path(checkpoint_path)
    if not ckpt_path.exists():
        raise FileNotFoundError(f"Checkpoint not found: {ckpt_path}")

    if expected_sha256 is not None:
        actual = file_sha256(ckpt_path)
        if actual.lower() != expected_sha256.lower():
            raise RuntimeError(
                f"Checkpoint checksum mismatch for {ckpt_path}. "
                f"Expected={expected_sha256}, Actual={actual}"
            )

    try:
        return torch.load(str(ckpt_path), map_location=map_location, weights_only=True)
    except Exception as exc:
        raise RuntimeError(
            "Secure checkpoint load failed with weights_only=True. "
            "Unsafe fallback is disabled by policy."
        ) from exc
