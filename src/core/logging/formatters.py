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
from typing import Any, Dict, NotRequired, TypedDict, Union

from protocols.ogx.encoding.json.encoder import OGxJsonEncoder

from .log_settings import LogComponent


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

    # Required base fields
    level: str
    component: str
    message: str
    timestamp: str

    # Process and thread info
    process: ProcessInfo
    thread: ThreadInfo

    # Custom fields - all optional
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
    extra: dict[str, Any]


class BaseFormatter(logging.Formatter):
    """Base formatter with common functionality."""

    def __init__(
        self,
        component: LogComponent,
        include_timestamp: bool = True,
        include_process: bool = True,
        include_thread: bool = True,
    ):
        super().__init__()
        self.component = component
        self.include_timestamp = include_timestamp
        self.include_process = include_process
        self.include_thread = include_thread
        self.encoder = OGxJsonEncoder()  # Initialize encoder

    def get_log_data(self, record: logging.LogRecord) -> Dict[str, Any]:
        """Get base log data as dictionary.

        Args:
            record: The log record to format

        Returns:
            Dictionary containing log data
        """
        data: Dict[str, Any] = {
            "level": record.levelname,
            "component": self.component.value,
            "message": record.getMessage(),
        }

        if self.include_timestamp:
            data["timestamp"] = datetime.fromtimestamp(record.created).isoformat()
        if self.include_process:
            data["process"] = {"name": record.processName, "id": record.process}
        if self.include_thread:
            data["thread"] = {"name": record.threadName, "id": record.thread}

        # Handle extra attributes safely
        extra = getattr(record, "extra", {})
        if extra:
            data["extra"] = extra

        return data

    def formatTime(self, record: logging.LogRecord, datefmt: str | None = None) -> str:
        """Format the time of the log record.

        Args:
            record: The log record to format
            datefmt: Optional datetime format string

        Returns:
            Formatted timestamp string
        """
        return datetime.fromtimestamp(record.created).isoformat()

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON string.

        Args:
            record: The log record to format

        Returns:
            JSON string representation of the log data
        """
        data: Dict[str, Any] = self.get_log_data(record)
        try:
            return self.encoder.encode(data)
        except Exception as e:
            return json.dumps(
                {
                    "error": f"Failed to serialize log message: {str(e)}",
                    "original_message": str(data),
                },
                default=str,
            )


class ProtocolFormatter(BaseFormatter):
    """Formatter for protocol-related logs."""

    def get_log_data(self, record: logging.LogRecord) -> Dict[str, Any]:
        """Get protocol-specific log data.

        Args:
            record: The log record to format

        Returns:
            Dictionary containing log data with protocol fields
        """
        data = super().get_log_data(record)

        message_id = getattr(record, "message_id", None)
        if message_id:
            data["message_id"] = message_id

        validation_errors = getattr(record, "validation_errors", None)
        if validation_errors:
            data["validation_errors"] = validation_errors

        return data


class APIFormatter(BaseFormatter):
    """Formatter for API endpoint logs."""

    def get_log_data(self, record: logging.LogRecord) -> Dict[str, Any]:
        """Get API-specific log data.

        Args:
            record: The log record to format

        Returns:
            Dictionary containing log data with API fields
        """
        data = super().get_log_data(record)

        # Add API-specific fields if present
        for field in ["request_id", "endpoint", "method", "status_code", "duration_ms"]:
            value = getattr(record, field, None)
            if value is not None:
                data[field] = value

        return data


class SecurityFormatter(BaseFormatter):
    """Formatter for security and auth logs."""

    SENSITIVE_FIELDS = {"password", "token", "secret", "key"}

    def _sanitize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Remove sensitive information from log data."""
        sanitized = {}
        for key, value in data.items():
            if any(sensitive in key.lower() for sensitive in self.SENSITIVE_FIELDS):
                sanitized[key] = "[REDACTED]"
            elif isinstance(value, dict):
                sanitized[key] = json.dumps(self._sanitize_data(value))
            else:
                sanitized[key] = value
        return sanitized

    def get_log_data(self, record: logging.LogRecord) -> Dict[str, Any]:
        """Get security-specific log data.

        Args:
            record: The log record to format

        Returns:
            Dictionary containing log data with security fields
        """
        data = super().get_log_data(record)

        # Handle auth_info if present
        auth_info = getattr(record, "auth_info", None)
        if isinstance(auth_info, dict):
            data["auth_info"] = self._sanitize_data(auth_info)

        # Handle security event if present
        security_event = getattr(record, "security_event", None)
        if isinstance(security_event, str):
            data["security_event"] = security_event

        return data

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON string with sanitized data.

        Args:
            record: The log record to format

        Returns:
            JSON string representation of the sanitized log data
        """
        try:
            data = self.get_log_data(record)
            return self.encoder.encode(data)
        except Exception as e:
            return self.encoder.encode(
                {
                    "error": f"Failed to serialize log message: {str(e)}",
                    "original_message": str(data),
                }
            )


class MetricsFormatter(BaseFormatter):
    """Formatter for metrics and monitoring logs."""

    def get_log_data(self, record: logging.LogRecord) -> Dict[str, Any]:
        """Get metrics-specific log data.

        Args:
            record: The log record to format

        Returns:
            Dictionary containing log data with metrics fields
        """
        data = super().get_log_data(record)

        metric_name = getattr(record, "metric_name", None)
        if metric_name is not None:
            data["metric"] = {
                "name": metric_name,
                "value": getattr(record, "metric_value", None),
                "unit": getattr(record, "metric_unit", None),
                "tags": getattr(record, "metric_tags", {}),
            }

        return data


class JsonFormatter(logging.Formatter):
    """Formatter for JSON logs using OGx JSON encoder."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the JSON formatter.

        Args:
            *args: Positional arguments for Formatter
            **kwargs: Keyword arguments for Formatter
        """
        super().__init__(*args, **kwargs)
        self.encoder = OGxJsonEncoder()

    def format(self, record: logging.LogRecord) -> str:
        """
        Format the log record using OGx JSON encoder.

        Args:
            record: LogRecord instance to format

        Returns:
            str: JSON formatted log string using OGx encoding
        """
        message_dict: Dict[str, Any] = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }

        # Safely get extra fields if they exist
        extra = getattr(record, "extra", {})
        if extra:
            message_dict["extra"] = extra

        try:
            return self.encoder.encode(message_dict)
        except Exception as e:
            return self.encoder.encode(
                {
                    "error": f"Failed to serialize log message: {str(e)}",
                    "original_message": str(message_dict),
                }
            )
