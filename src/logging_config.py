"""Central logging configuration for SVAMITVA pipeline modules."""

from __future__ import annotations

import logging
import os
import sys


def configure_logging(level: str | None = None) -> None:
    """Configure root logging once for CLI and library use."""
    log_level = (level or os.getenv("SVAMITVA_LOG_LEVEL", "INFO")).upper()
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
        stream=sys.stderr,
        force=True,
    )


def get_logger(name: str) -> logging.Logger:
    if not logging.getLogger().handlers:
        configure_logging()
    return logging.getLogger(name)
