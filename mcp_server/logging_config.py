"""
Logging configuration for SignalForge.

Configures a simple, production-friendly logging format that logs to stdout.
"""

from __future__ import annotations

import logging
import sys

_LOGGER_CONFIGURED = False


def setup_logging(level: str = "INFO") -> None:
    """
    Configure global logging once.

    Args:
        level: Log level name (e.g. "DEBUG", "INFO", "WARNING", "ERROR").
    """
    global _LOGGER_CONFIGURED

    if _LOGGER_CONFIGURED:
        return

    numeric_level = getattr(logging, level.upper(), logging.INFO)

    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    _LOGGER_CONFIGURED = True
