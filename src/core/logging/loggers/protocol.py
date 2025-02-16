"""Protocol-specific logger configuration."""

import logging
from typing import Optional

from ..log_settings import LogComponent, LoggingConfig
from .factory import get_logger_factory


def get_protocol_logger(
    config: Optional[LoggingConfig] = None,
) -> logging.Logger:
    """Get logger for protocol operations.

    Args:
        config: Optional logging configuration

    Returns:
        Configured logger instance
    """
    factory = get_logger_factory(config)
    logger = factory.get_logger(
        component=LogComponent.PROTOCOL,
        use_file=True,
        use_stream=True,
        use_syslog=False,
    )

    return logger
