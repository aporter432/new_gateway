"""File-based logging handler configuration."""

import logging
import os
from pathlib import Path
from typing import Optional

from ..log_settings import LogComponent, LoggingConfig
from . import get_formatter


def get_file_handler(
    component: LogComponent,
    config: LoggingConfig,
    filename: Optional[str] = None,
) -> logging.Handler:
    """Create a file handler for logging.

    Args:
        component: Logging component to create handler for
        config: Logging configuration
        filename: Optional specific filename to use

    Returns:
        Configured file handler
    """
    # Get project root directory and create logs directory
    project_root = Path(__file__).parent.parent.parent.parent.parent
    logs_dir = project_root / "logs"
    os.makedirs(logs_dir, exist_ok=True)

    # Use component name for log file if not specified
    if not filename:
        filename = str(logs_dir / f"{component.name.lower()}.log")

    handler = logging.FileHandler(filename)
    handler.setFormatter(get_formatter(component))
    return handler
