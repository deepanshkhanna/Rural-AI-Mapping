"""Runtime platform configuration loader.

This module centralizes classes, splits, and shared runtime knobs to prevent
configuration drift across training, evaluation, and inference entry points.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


@dataclass(frozen=True)
class ClassSpec:
    id: int
    name: str
    color_rgb: tuple[int, int, int]


@dataclass(frozen=True)
class PlatformConfig:
    version: str
    classes: tuple[ClassSpec, ...]
    train_tiffs: tuple[str, ...]
    val_tiffs: tuple[str, ...]
    training: dict
    evaluation: dict
    security: dict
    geospatial: dict
    dataset_sources: tuple[dict, ...] = ()

    @property
    def num_classes(self) -> int:
        return len(self.classes)

    @property
    def class_names(self) -> dict[int, str]:
        return {c.id: c.name for c in self.classes}


def _default_config_path() -> Path:
    root = Path(__file__).resolve().parents[2]
    env_path = os.getenv("SVAMITVA_CONFIG_PATH")
    if env_path:
        return Path(env_path)
    return root / "config" / "platform_config.v1.json"


@lru_cache(maxsize=1)
def load_platform_config(config_path: str | None = None) -> PlatformConfig:
    if config_path is None:
        config_path = os.getenv("SVAMITVA_CONFIG_PATH")
    path = Path(config_path) if config_path else _default_config_path()
    raw = json.loads(path.read_text(encoding="utf-8"))

    classes = tuple(
        ClassSpec(
            id=int(row["id"]),
            name=str(row["name"]),
            color_rgb=tuple(int(v) for v in row["color_rgb"]),
        )
        for row in raw["classes"]
    )

    return PlatformConfig(
        version=str(raw["version"]),
        classes=classes,
        train_tiffs=tuple(raw["splits"]["train_tiffs"]),
        val_tiffs=tuple(raw["splits"]["val_tiffs"]),
        training=dict(raw.get("training", {})),
        evaluation=dict(raw.get("evaluation", {})),
        security=dict(raw.get("security", {})),
        geospatial=dict(raw.get("geospatial", {})),
        dataset_sources=tuple(raw.get("dataset_sources", [])),
    )
