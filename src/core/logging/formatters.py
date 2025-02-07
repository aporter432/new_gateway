"""Custom log formatters for different components.

This module provides formatters for:
- Protocol logs (with message IDs and validation details)
- System logs (with process and thread info)
- API logs (with request IDs and endpoints)
- Infrastructure logs (with component states)
- Security logs (with sanitized sensitive data)

Type Definitions:
    LogData: Base type for all log entries
    ProcessInfo: Process-related information
    ThreadInfo: Thread-related information
    MetricInfo: Metrics and monitoring data
"""

# pylint: disable=no-member

import json
import logging
from datetime import datetime
from typing import Any, TypedDict, NotRequired, cast, Union

from .config import LogComponent


class ProcessInfo(TypedDict):
    """Process information in log entries."""

    name: str
    id: int


class ThreadInfo(TypedDict):
    """Thread information in log entries."""

    name: str
    id: int


class MetricInfo(TypedDict):
    """Metric information for monitoring."""

    name: str
    value: NotRequired[Union[str, int, float, None]]
    unit: NotRequired[Union[str, None]]
    tags: NotRequired[dict[str, Union[str, int, float]]]


class LogData(TypedDict, total=False):
    """Base structure for all log entries."""

    level: str
    component: str
    message: str
    timestamp: str
    process: ProcessInfo
    thread: ThreadInfo
    # Custom fields
    message_id: str
    validation_errors: list[str]
    request_id: str
    endpoint: str
    method: str
    status_code: int
    duration_ms: int
    auth_info: dict[str, Any]
    security_event: str
    metric: MetricInfo


class BaseFormatter(logging.Formatter):
    """Base formatter with common functionality.

    Provides basic log formatting with configurable fields:
    - Timestamp (ISO format with timezone)
    - Process information
    - Thread information
    - Component identification
    """

    def __init__(
        self,
        component: LogComponent,
        include_timestamp: bool = True,
        include_process: bool = True,
        include_thread: bool = True,
    ):
        self.component = component
        self.include_timestamp = include_timestamp
        self.include_process = include_process
        self.include_thread = include_thread
        super().__init__()

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with component-specific details.

        Args:
            record: The log record to format

        Returns:
            JSON string representation of the log data
        """
        data: LogData = {
            "level": record.levelname,
            "component": self.component.value,
            "message": record.getMessage(),
        }

        if self.include_timestamp:
            data["timestamp"] = datetime.fromtimestamp(record.created).isoformat()
        if self.include_process:
            data["process"] = {"name": record.processName, "id": record.process}  # type: ignore
        if self.include_thread:
            data["thread"] = {"name": record.threadName, "id": record.thread}  # type: ignore

        # Handle extra attributes safely
        extra = getattr(record, "extra", {})
        if extra:
            data.update(cast(LogData, extra))

        return json.dumps(data)  # type: ignore[no-any-return]


class ProtocolFormatter(BaseFormatter):
    """Formatter for protocol-related logs.

    Adds protocol-specific fields:
    - Message ID for tracking
    - Validation errors if present
    """

    def format(self, record: logging.LogRecord) -> str:
        """Add protocol-specific fields.

        Args:
            record: The log record to format

        Returns:
            JSON string with protocol-specific fields
        """
        data: LogData = json.loads(super().format(record))  # type: ignore[no-any-return]

        message_id = getattr(record, "message_id", None)
        if message_id:
            data["message_id"] = message_id

        validation_errors = getattr(record, "validation_errors", None)
        if validation_errors:
            data["validation_errors"] = validation_errors

        return json.dumps(data)  # type: ignore[no-any-return]


class APIFormatter(BaseFormatter):
    """Formatter for API endpoint logs.

    Adds API-specific fields:
    - Request ID for tracing
    - Endpoint information
    - HTTP method
    - Status code
    - Request duration
    """

    def format(self, record: logging.LogRecord) -> str:
        """Add API-specific fields.

        Args:
            record: The log record to format

        Returns:
            JSON string with API-specific fields
        """
        data: LogData = json.loads(super().format(record))  # type: ignore[no-any-return]

        # Add API-specific fields if present
        for field in ["request_id", "endpoint", "method", "status_code", "duration_ms"]:
            value = getattr(record, field, None)
            if value is not None:
                data[field] = value  # type: ignore[literal-required]

        return json.dumps(data)  # type: ignore[no-any-return]


class SecurityFormatter(BaseFormatter):
    """Formatter for security and auth logs.

    Features:
    - Automatic sanitization of sensitive fields
    - Security event tracking
    - Auth information logging
    """

    SENSITIVE_FIELDS = {"password", "token", "secret", "key"}

    def _sanitize_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """Remove sensitive information from log data.

        Args:
            data: Dictionary containing potentially sensitive data

        Returns:
            Sanitized copy of the data
        """
        sanitized = {}
        for key, value in data.items():
            if any(sensitive in key.lower() for sensitive in self.SENSITIVE_FIELDS):
                sanitized[key] = "[REDACTED]"
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_data(value)
            else:
                sanitized[key] = value
        return sanitized

    def format(self, record: logging.LogRecord) -> str:
        """Add security-specific fields with sanitization.

        Args:
            record: The log record to format

        Returns:
            JSON string with sanitized security fields
        """
        data: LogData = json.loads(super().format(record))  # type: ignore[no-any-return]

        auth_info = getattr(record, "auth_info", None)
        if auth_info:
            data["auth_info"] = self._sanitize_data(auth_info)

        security_event = getattr(record, "security_event", None)
        if security_event:
            data["security_event"] = security_event

        return json.dumps(data)  # type: ignore[no-any-return]


class MetricsFormatter(BaseFormatter):
    """Formatter for metrics and monitoring logs.

    Handles:
    - Metric names and values
    - Units of measurement
    - Custom tags
    """

    def format(self, record: logging.LogRecord) -> str:
        """Add metrics-specific fields.

        Args:
            record: The log record to format

        Returns:
            JSON string with metrics information
        """
        data: LogData = json.loads(super().format(record))  # type: ignore[no-any-return]

        metric_name = getattr(record, "metric_name", None)
        if metric_name is not None:
            data["metric"] = {
                "name": metric_name,
                "value": getattr(record, "metric_value", None),
                "unit": getattr(record, "metric_unit", None),
                "tags": getattr(record, "metric_tags", {}),
            }

        return json.dumps(data)  # type: ignore[no-any-return]
