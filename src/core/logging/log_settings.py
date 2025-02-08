"""Logging configuration for high-volume gateway operations.

Handles:
- Multiple customers (200+)
- High volume asset tracking (3000K+)
- Critical infrastructure monitoring
- Performance optimization
- Log rotation and retention
"""

import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

# Base paths with clear structure
LOG_DIR = Path("/var/log/gateway")  # Production logs
DEV_LOG_DIR = Path("logs")  # Development logs


# Component-specific settings
class LogComponent(str, Enum):
    """Core logging components."""

    PROTOCOL = "protocol"  # Protocol/message handling
    SYSTEM = "system"  # System operations
    INFRA = "infra"  # Infrastructure (DB, Redis, etc)
    API = "api"  # API endpoints
    AUTH = "auth"  # Authentication/security
    METRICS = "metrics"  # Performance metrics


@dataclass
class RotationPolicy:
    """Log rotation settings optimized for high volume."""

    max_bytes: int = 100 * 1024 * 1024  # 100MB per file
    backup_count: int = 10  # Keep 10 backup files
    compress: bool = True  # Compress old logs
    interval: int = 1  # Rotate daily
    utc: bool = True  # Use UTC for timestamps


@dataclass
class LoggerConfig:
    """Configuration for individual loggers."""

    name: str  # Logger name
    level: str  # Log level
    file_name: str  # Log file path
    rotation: RotationPolicy  # Rotation settings
    buffer_size: int = 1000  # Buffer size for batch logging
    flush_interval: float = 1.0  # Flush every second
    include_customer: bool = True  # Include customer context
    include_asset: bool = True  # Include asset context
    propagate: bool = False  # Don't propagate to parent


class LoggingConfig:
    """Central logging configuration."""

    def __init__(self, is_production: bool = False):
        """Initialize logging configuration.

        Args:
            is_production: Whether running in production
        """
        self.is_production = is_production
        self.base_dir = LOG_DIR if is_production else DEV_LOG_DIR
        self._ensure_log_dir()

        # Performance settings
        self.batch_size = 1000 if is_production else 100
        self.async_logging = is_production
        self.buffer_size = 10000 if is_production else 1000

        # Retention settings (days)
        self.retention = {
            LogComponent.PROTOCOL: 30,
            LogComponent.SYSTEM: 90,
            LogComponent.INFRA: 60,
            LogComponent.API: 30,
            LogComponent.AUTH: 365,  # Keep auth logs longer
            LogComponent.METRICS: 7,
        }

    def _ensure_log_dir(self) -> None:
        """Create log directories if they don't exist."""
        for component in LogComponent:
            os.makedirs(self.base_dir / component.value, exist_ok=True)

    def get_logger_config(self, component: LogComponent) -> LoggerConfig:
        """Get configuration for a specific component.

        Args:
            component: The logging component

        Returns:
            Component-specific configuration
        """
        return LoggerConfig(
            name=f"gateway.{component.value}",
            level="INFO" if self.is_production else "DEBUG",
            file_name=str(self.base_dir / component.value / "current.log"),
            rotation=RotationPolicy(
                max_bytes=(
                    200 * 1024 * 1024
                    if component in [LogComponent.PROTOCOL, LogComponent.METRICS]
                    else 100 * 1024 * 1024
                ),
                backup_count=20 if component == LogComponent.AUTH else 10,
            ),
            buffer_size=self.buffer_size,
            flush_interval=(
                0.5 if component in [LogComponent.PROTOCOL, LogComponent.METRICS] else 1.0
            ),
        )

    def get_log_path(self, component: LogComponent) -> Path:
        """Get the log file path for a component."""
        return self.base_dir / component.value / "current.log"

    @property
    def default_format(self) -> str:
        """Default log format with customer/asset context."""
        return (
            "%(asctime)s.%(msecs)03d | %(levelname)-8s | "
            "%(customer_id)s | %(asset_id)s | "
            "%(processName)s:%(process)d | "
            "%(threadName)s:%(thread)d | "
            "%(name)s | %(message)s"
        )

    @property
    def metrics_format(self) -> str:
        """Format string for metrics logging."""
        return "%(asctime)s | %(name)s | %(message)s"
