"""Stream handlers for console output."""

import logging
import sys
from typing import Optional, TextIO

from ..log_settings import LogComponent, LoggingConfig
from . import get_formatter


def get_stream_handler(
    component: LogComponent,
    config: LoggingConfig,
    stream: Optional[TextIO] = None,
    level: Optional[int] = None,
) -> logging.StreamHandler:
    """Create a stream handler for console output.

    Args:
        component: Logging component to create handler for
        config: Logging configuration
        stream: Optional stream to write to (defaults to stderr)
        level: Optional log level override

    Returns:
        Configured stream handler
    """
    handler = logging.StreamHandler(stream or sys.stderr)
    handler.setFormatter(get_formatter(component))

    if level is not None:
        handler.setLevel(level)

    return handler
