"""API-specific logger implementation."""

import logging
from typing import Optional

from ..log_settings import LogComponent


def get_api_logger(
    name: Optional[str] = None,
    include_metrics: bool = True,
) -> logging.Logger:
    """Get logger for API components.

    Args:
        name: Optional sub-component name
        include_metrics: Whether to include metrics handler

    Returns:
        Configured logger instance
    """
    from . import get_logger_factory

    factory = get_logger_factory()
    logger = factory.get_logger(
        LogComponent.API,
        use_syslog=True,  # API logs should go to syslog
    )

    if name:
        logger = logging.getLogger(f"{logger.name}.{name}")
        logger.parent = logger

    return logger
