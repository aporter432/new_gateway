"""Application-level logger implementation."""

import logging
from typing import Optional

from ..log_settings import LogComponent, LoggingConfig


def get_app_logger(
    config: Optional[LoggingConfig] = None,
    name: Optional[str] = None,
) -> logging.Logger:
    """Get logger for the main application.

    Args:
        config: Optional logging configuration
        name: Optional sub-component name

    Returns:
        Configured logger instance
    """
    from . import get_logger_factory

    factory = get_logger_factory(config)
    # Use SYSTEM component as it's the closest match for application-level logging
    logger = factory.get_logger(
        LogComponent.SYSTEM,
        use_syslog=True,
    )

    if name:
        logger = logging.getLogger(f"{logger.name}.{name}")
        logger.parent = logger

    return logger
