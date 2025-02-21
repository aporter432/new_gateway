"""Base handlers for logging implementation.

This module provides base handler functionality and common utilities
for all specialized handlers (file, stream, syslog, metrics).
"""

from ..formatters import (
    APIFormatter,
    BaseFormatter,
    MetricsFormatter,
    ProtocolFormatter,
    SecurityFormatter,
)
from ..log_settings import LogComponent


def get_formatter(component: LogComponent) -> BaseFormatter:
    """Get the appropriate formatter for a component.

    Args:
        component: The logging component to get formatter for

    Returns:
        Configured formatter instance for the component
    """
    formatters = {
        LogComponent.API: APIFormatter,
        LogComponent.PROTOCOL: ProtocolFormatter,
        LogComponent.AUTH: SecurityFormatter,
        LogComponent.METRICS: MetricsFormatter,
    }
    formatter_class = formatters.get(component, BaseFormatter)
    return formatter_class(component=component)
