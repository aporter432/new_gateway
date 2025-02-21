"""Base handlers for logging implementation.

This module provides base handler functionality and common utilities
for all specialized handlers (file, stream, syslog, metrics).
"""

from .formatter_factory import get_formatter

__all__ = ["get_formatter"]
