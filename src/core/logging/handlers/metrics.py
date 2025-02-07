"""Metrics handlers for monitoring system integration."""

import logging
from abc import abstractmethod
from typing import Optional, Protocol, TypedDict, Union

from ..log_settings import LogComponent, LoggingConfig
from ..records import GatewayLogRecord
from . import get_formatter


class MetricData(TypedDict, total=False):
    """Metric data structure."""

    name: str
    value: Union[int, float, str]
    type: str
    tags: dict[str, Union[str, int, float]]


class MetricsBackend(Protocol):
    """Protocol for metrics backend implementations."""

    @abstractmethod
    def increment(self, name: str, value: float = 1, tags: Optional[dict] = None) -> None:
        """Increment a counter metric."""

    @abstractmethod
    def gauge(self, name: str, value: float, tags: Optional[dict] = None) -> None:
        """Set a gauge metric value."""

    @abstractmethod
    def timing(self, name: str, value: float, tags: Optional[dict] = None) -> None:
        """Record a timing metric."""


class MetricsHandler(logging.Handler):
    """Handler that forwards metrics to monitoring system."""

    def __init__(self, backend: MetricsBackend):
        """Initialize with metrics backend.

        Args:
            backend: Metrics collection backend
        """
        super().__init__()
        self.backend = backend

    def emit(self, record: GatewayLogRecord) -> None:
        """Forward metric to backend system.

        Args:
            record: Log record containing metric data
        """
        try:
            if not hasattr(record, "metric_name") or record.metric_name is None:
                return

            metric_name: str = record.metric_name  # Type assertion after None check
            metric_value = getattr(record, "metric_value", 1)
            metric_type = getattr(record, "metric_type", "counter")
            tags = getattr(record, "metric_tags", {})

            if metric_type == "counter":
                self.backend.increment(metric_name, metric_value, tags)
            elif metric_type == "gauge":
                self.backend.gauge(metric_name, metric_value, tags)
            elif metric_type == "timing":
                self.backend.timing(metric_name, metric_value, tags)

        except (AttributeError, ValueError, TypeError):
            self.handleError(record)


def get_metrics_handler(
    component: LogComponent,
    _config: LoggingConfig,  # Prefix with _ to indicate intentionally unused
    backend: MetricsBackend,
) -> logging.Handler:
    """Create a metrics handler.

    Args:
        component: Logging component to create handler for
        _config: Logging configuration (unused but kept for consistency)
        backend: Metrics collection backend

    Returns:
        Configured metrics handler
    """
    handler = MetricsHandler(backend)
    handler.setFormatter(get_formatter(component))
    return handler
