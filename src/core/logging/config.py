"""Base logging configuration for the gateway.

This module defines:
- Log file locations and naming
- Default log levels per component
- Rotation policies
- Basic configuration settings
"""

import os
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, Optional

# Base paths
LOG_DIR = Path("/var/log/gateway")  # Production logs
DEV_LOG_DIR = Path("logs")  # Development logs


# Component-specific log files
class LogComponent(str, Enum):
    """Available logging components."""

    PROTOCOL = "protocol"
    SYSTEM = "system"
    INFRA = "infrastructure"
    API = "api"
    AUTH = "auth"
    METRICS = "metrics"


@dataclass
class RotationPolicy:
    """Log rotation settings."""

    max_bytes: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    compress: bool = True
    utc_timestamps: bool = True


@dataclass
class LoggerConfig:
    """Configuration for individual loggers."""

    name: str
    level: str
    file_name: str
    rotation: RotationPolicy
    propagate: bool = False
    include_timestamp: bool = True
    include_process: bool = True
    include_thread: bool = True


class LoggingConfig:
    """Central logging configuration."""

    def __init__(self, is_production: bool = False):
        self.is_production = is_production
        self.base_dir = LOG_DIR if is_production else DEV_LOG_DIR
        self.date_format = "%Y-%m-%d %H:%M:%S.%f %z"
        self._ensure_log_dir()

    def _ensure_log_dir(self) -> None:
        """Ensure log directory exists."""
        os.makedirs(self.base_dir, exist_ok=True)

    def get_logger_config(self, component: LogComponent) -> LoggerConfig:
        """Get configuration for specific component."""
        return LoggerConfig(
            name=f"gateway.{component.value}",
            level="INFO" if self.is_production else "DEBUG",
            file_name=self.base_dir / f"{component.value}.log",
            rotation=RotationPolicy(),
        )

    def get_log_path(self, component: LogComponent) -> Path:
        """Get full path for component log file."""
        return self.base_dir / f"{component.value}.log"

    @property
    def default_format(self) -> str:
        """Default log format string."""
        return (
            "%(asctime)s | %(levelname)-8s | "
            "%(processName)s:%(process)d | "
            "%(threadName)s:%(thread)d | "
            "%(name)s | %(message)s"
        )

    @property
    def metrics_format(self) -> str:
        """Format string for metrics logging."""
        return "%(asctime)s | %(name)s | %(message)s"
