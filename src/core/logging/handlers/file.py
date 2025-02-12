"""File-based logging handler configuration."""

import logging
import os
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
    # Ensure logs directory exists
    os.makedirs("/app/logs", exist_ok=True)

    # Use component name for log file if not specified
    if not filename:
        filename = f"/app/logs/{component.name.lower()}.log"

    handler = logging.FileHandler(filename)
    handler.setFormatter(get_formatter(component))
    return handler
