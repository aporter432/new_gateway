"""Metrics collection and monitoring system.

This package provides:
- Metric collection and storage backends
- Domain-specific metric collectors
- FastAPI integration middleware
- Prometheus integration
- Custom exceptions for error handling
"""

from .backends.base import MetricsBackend
from .backends.prometheus import PrometheusBackend
from .collectors.api import APIMetrics
from .collectors.auth import AuthMetrics
from .collectors.message import MessageMetrics
from .collectors.system import SystemMetrics
from .exceptions import (
    BackendError,
    CollectorError,
    MetricsError,
    SystemMetricsError,
)
from .middleware.fastapi import MetricsMiddleware

__all__ = [
    # Backends
    "MetricsBackend",
    "PrometheusBackend",
    # Collectors
    "APIMetrics",
    "AuthMetrics",
    "MessageMetrics",
    "SystemMetrics",
    # Middleware
    "MetricsMiddleware",
    # Exceptions
    "MetricsError",
    "CollectorError",
    "BackendError",
    "SystemMetricsError",
]
