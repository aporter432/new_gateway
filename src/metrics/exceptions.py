"""Exceptions for metrics collection and monitoring.

This module defines custom exceptions for:
- Metrics collection failures
- Backend storage errors
- Configuration issues
- System metric collection errors
"""


class MetricsError(Exception):
    """Base exception for all metrics-related errors."""

    def __init__(self, message: str, error_code: int | None = None):
        self.error_code = error_code
        super().__init__(message)


class CollectorError(MetricsError):
    """Raised when a metrics collector encounters an error.

    Error codes:
    - 1001: Collection initialization failed
    - 1002: Collection task failed
    - 1003: Invalid metric value
    - 1004: Invalid metric name
    - 1005: Collection interval error
    """

    INIT_FAILED = 1001
    COLLECTION_FAILED = 1002
    INVALID_VALUE = 1003
    INVALID_NAME = 1004
    INTERVAL_ERROR = 1005


class BackendError(MetricsError):
    """Raised when a metrics backend encounters an error.

    Error codes:
    - 2001: Backend initialization failed
    - 2002: Storage operation failed
    - 2003: Invalid metric type
    - 2004: Invalid tag format
    - 2005: Connection error
    """

    INIT_FAILED = 2001
    STORAGE_FAILED = 2002
    INVALID_TYPE = 2003
    INVALID_TAG = 2004
    CONNECTION_ERROR = 2005


class SystemMetricsError(CollectorError):
    """Raised when system metrics collection fails.

    Error codes:
    - 3001: Process metrics unavailable
    - 3002: System metrics unavailable
    - 3003: IO metrics unavailable
    - 3004: Permission denied
    - 3005: Resource not found
    """

    PROCESS_UNAVAILABLE = 3001
    SYSTEM_UNAVAILABLE = 3002
    IO_UNAVAILABLE = 3003
    PERMISSION_DENIED = 3004
    RESOURCE_NOT_FOUND = 3005
