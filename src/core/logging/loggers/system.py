"""System-wide logger implementation."""

import logging
from typing import Optional

from ..log_settings import LogComponent
from . import get_logger_factory


def get_system_logger(
    name: Optional[str] = None,
    include_metrics: bool = True,
) -> logging.Logger:
    """Get logger for system-wide components.

    Args:
        name: Optional sub-component name (e.g., 'startup', 'shutdown')
        include_metrics: Whether to include metrics handler

    Returns:
        Configured logger instance
    """
    factory = get_logger_factory()
    logger = factory.get_logger(
        LogComponent.SYSTEM,
        use_file=True,
        use_stream=True,
        use_syslog=True,  # System logs should go to all outputs for visibility
    )

    if name:
        logger = logging.getLogger(f"{logger.name}.{name}")
        logger.parent = logger

    return logger
