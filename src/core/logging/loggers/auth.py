"""Authentication-specific logger implementation."""

import logging
from typing import Optional

from ..log_settings import LogComponent


def get_auth_logger(
    name: Optional[str] = None,
    include_metrics: bool = True,
) -> logging.Logger:
    """Get logger for authentication components.

    Args:
        name: Optional sub-component name
        include_metrics: Whether to include metrics handler

    Returns:
        Configured logger instance
    """
    from . import get_logger_factory

    factory = get_logger_factory()
    logger = factory.get_logger(
        LogComponent.AUTH,
        use_syslog=True,  # Auth logs should go to syslog for security monitoring
    )

    if name:
        logger = logging.getLogger(f"{logger.name}.{name}")
        logger.parent = logger

    return logger
