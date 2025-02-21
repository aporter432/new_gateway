"""Syslog handlers for system logging integration."""

import logging
import logging.handlers
from typing import Optional

from ..log_settings import LogComponent, LoggingConfig
from . import get_formatter


def get_syslog_handler(
    component: LogComponent,
    config: LoggingConfig,
    address: Optional[tuple[str, int]] = None,
    facility: int = logging.handlers.SysLogHandler.LOG_LOCAL0,
) -> logging.Handler:
    """Create a syslog handler.

    Args:
        component: Logging component to create handler for
        config: Logging configuration
        address: Optional (host, port) tuple for remote syslog
        facility: Syslog facility to use

    Returns:
        Configured syslog handler
    """
    try:
        # Try local syslog first
        handler = logging.handlers.SysLogHandler(
            address=address or "/dev/log",
            facility=facility,
        )
    except (FileNotFoundError, ConnectionError):
        # Fall back to UDP syslog
        handler = logging.handlers.SysLogHandler(
            address=address or ("localhost", 514),
            facility=facility,
        )

    handler.setFormatter(get_formatter(component))
    return handler
