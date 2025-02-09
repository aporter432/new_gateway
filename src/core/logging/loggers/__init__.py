"""Base logger factory and configuration.

This module provides:
- Logger factory for creating component-specific loggers
- Common logging setup and configuration
- Handler management
"""

from ..handlers.file import get_file_handler
from ..handlers.metrics import get_metrics_handler
from ..handlers.stream import get_stream_handler
from ..handlers.syslog import get_syslog_handler
from ..log_settings import LogComponent, LoggingConfig
from .api import get_api_logger
from .auth import get_auth_logger
from .factory import LoggerFactory, get_logger_factory
from .infra import get_infra_logger
from .protocol import get_protocol_logger
from .system import get_system_logger

__all__ = [
    "LoggerFactory",
    "get_logger_factory",
    "get_api_logger",
    "get_auth_logger",
    "get_infra_logger",
    "get_protocol_logger",
    "get_system_logger",
    "get_file_handler",
    "get_metrics_handler",
    "get_stream_handler",
    "get_syslog_handler",
    "LogComponent",
    "LoggingConfig",
]
