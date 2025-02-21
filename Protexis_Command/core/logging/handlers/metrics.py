"""Metrics handlers for monitoring system integration."""

import asyncio
import logging
from typing import Any, Protocol, TypedDict, Union, runtime_checkable

from metrics.backends.base import MetricsBackend as BaseMetricsBackend

from ..log_settings import LogComponent, LoggingConfig
from . import get_formatter

__all__ = ["MetricsHandler", "get_metrics_handler"]


class MetricData(TypedDict, total=False):
    """Metric data structure."""

    name: str
    value: Union[int, float, str]
    type: str
    tags: dict[str, Union[str, int, float]]


@runtime_checkable
class GatewayLogRecord(Protocol):
    """Protocol for log records with metric data."""

    metric_name: str
    metric_value: Any
    metric_type: str
    metric_tags: dict[str, str]


class MetricsHandler(logging.Handler):
    """Handler for forwarding metrics to collection backend."""

    def __init__(self, backend: BaseMetricsBackend):
        """Initialize with metrics backend.

        Args:
            backend: Metrics collection backend
        """
        super().__init__()
        self.backend = backend
        self.loop = asyncio.get_event_loop()

    def emit(self, record: logging.LogRecord) -> None:
        """Forward metric to backend system.

        Args:
            record: Log record containing metric data
        """
        try:
            # Check if record has metric data using Protocol
            if not isinstance(record, GatewayLogRecord):
                return

            metric_name: str = record.metric_name
            metric_value = record.metric_value
            metric_type = record.metric_type
            metric_tags = record.metric_tags

            # Create coroutine based on metric type
            coro = None
            if metric_type == "counter":
                coro = self.backend.increment(metric_name, metric_value, metric_tags)
            elif metric_type == "gauge":
                coro = self.backend.gauge(metric_name, metric_value, metric_tags)
            elif metric_type == "histogram":
                coro = self.backend.histogram(metric_name, metric_value, metric_tags)
            elif metric_type == "summary":
                coro = self.backend.summary(metric_name, metric_value, metric_tags)

            # Schedule coroutine if we have one
            if coro is not None:
                self.loop.create_task(coro)

        except Exception:
            self.handleError(record)


def get_metrics_handler(
    component: LogComponent,
    _config: LoggingConfig,  # Prefix with _ to indicate intentionally unused
    backend: BaseMetricsBackend,
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
