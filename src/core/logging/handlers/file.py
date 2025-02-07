"""File handlers with rotation support.

This module provides file-based logging handlers with:
- Size-based rotation
- Compression of old logs
- UTC timestamp support
- Component-specific formatting
"""

import logging
import logging.handlers
from pathlib import Path
from typing import Optional

from ..log_settings import LogComponent, LoggingConfig
from . import get_formatter


def get_file_handler(
    component: LogComponent,
    config: LoggingConfig,
    filename: Optional[Path] = None,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    encoding: str = "utf-8",
) -> logging.Handler:
    """Create a rotating file handler.

    Args:
        component: Logging component to create handler for
        config: Logging configuration
        filename: Optional specific log file path
        max_bytes: Maximum size before rotation
        backup_count: Number of backup files to keep
        encoding: File encoding to use

    Returns:
        Configured rotating file handler
    """
    # Use component-specific path if filename not provided
    log_path = filename or config.get_log_path(component)

    # Ensure parent directory exists
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Create rotating handler
    handler = logging.handlers.RotatingFileHandler(
        filename=str(log_path),
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding=encoding,
    )

    # Get appropriate formatter
    handler.setFormatter(get_formatter(component))

    # Set level from config
    logger_config = config.get_logger_config(component)
    handler.setLevel(logging.getLevelName(logger_config.level))

    return handler
