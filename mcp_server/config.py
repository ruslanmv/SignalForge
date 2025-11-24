"""
Central configuration for SignalForge.

This wraps the existing YAML config (config/config.yaml) and environment
variables into a single Settings object used by the MCP server.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional
import os

import yaml

DEFAULT_CONFIG_RELATIVE_PATH = "config/config.yaml"


@dataclass
class Settings:
    """
    Application settings loaded from YAML plus environment variables.

    Attributes:
        project_root: Root directory of the project (repository root).
        config: Parsed YAML configuration as a nested dict.
        environment: Logical environment name (e.g. "dev", "staging", "prod").
        log_level: Logging level string (DEBUG/INFO/WARNING/ERROR).
    """

    project_root: Path
    config: Dict[str, Any]
    environment: str = "production"
    log_level: str = "INFO"

    @property
    def output_dir(self) -> Path:
        """Directory where crawler outputs TXT files."""
        return self.project_root / "output"

    @property
    def config_path(self) -> Path:
        """Resolved path to the main YAML config file."""
        return self.project_root / DEFAULT_CONFIG_RELATIVE_PATH

    @classmethod
    def load(
        cls,
        project_root: Optional[str] = None,
        config_path: Optional[str] = None,
    ) -> "Settings":
        """
        Load settings from YAML and environment variables.

        Precedence:
        1. Function arguments (project_root/config_path)
        2. Environment variables (SIGNALFORGE_*)
        3. Defaults based on the location of this file.
        """
        # Resolve project root
        if project_root:
            root = Path(project_root).resolve()
        else:
            # mcp_server/ is one level below repo root
            root = Path(__file__).resolve().parent.parent

        # Resolve config path
        if config_path:
            cfg_path = Path(config_path).resolve()
        else:
            cfg_path = root / DEFAULT_CONFIG_RELATIVE_PATH

        if not cfg_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {cfg_path}")

        with cfg_path.open("r", encoding="utf-8") as f:
            raw_cfg = yaml.safe_load(f) or {}

        # Environment and log level
        environment = os.getenv("SIGNALFORGE_ENV", "production")

        log_level = (
            os.getenv("SIGNALFORGE_LOG_LEVEL")
            or (raw_cfg.get("logging", {}) or {}).get("level", "INFO")
        )

        return cls(
            project_root=root,
            config=raw_cfg,
            environment=environment,
            log_level=log_level,
        )
