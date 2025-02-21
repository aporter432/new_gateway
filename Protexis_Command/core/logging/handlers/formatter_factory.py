"""Formatter factory for logging handlers.

This module provides factory functions for creating appropriate formatters
based on logging components.
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
