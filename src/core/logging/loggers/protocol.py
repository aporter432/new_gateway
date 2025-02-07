"""Protocol-specific logger implementation."""

import logging
from typing import Optional

from ..log_settings import LogComponent
from . import get_logger_factory


def get_protocol_logger(
    name: Optional[str] = None,
    include_metrics: bool = True,
) -> logging.Logger:
    """Get logger for protocol components.

    Args:
        name: Optional sub-component name
        include_metrics: Whether to include metrics handler

    Returns:
        Configured logger instance
    """
    factory = get_logger_factory()
    logger = factory.get_logger(
        LogComponent.PROTOCOL,
        use_syslog=True,  # Protocol logs should go to syslog for monitoring
    )

    if name:
        logger = logging.getLogger(f"{logger.name}.{name}")
        logger.parent = logger

    return logger
