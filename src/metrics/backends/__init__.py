"""Metric storage backend implementations.

This module provides:
- Backend protocol definition
- Factory functions for backend creation
- Common backend utilities
"""

from .base import MetricsBackend
from .prometheus import PrometheusBackend

__all__ = ["MetricsBackend", "PrometheusBackend"]
