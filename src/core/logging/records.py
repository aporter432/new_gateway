"""Custom LogRecord types for extended logging functionality."""

import logging
from typing import Any, Dict, Optional, TypedDict, Union


class MetricInfo(TypedDict, total=False):
    """Metric information structure."""

    name: str
    value: Union[int, float, str]
    type: str  # "counter", "gauge", or "timing"
    unit: Optional[str]
    tags: Dict[str, Union[str, int, float]]


class APIInfo(TypedDict, total=False):
    """API request information structure."""

    request_id: str
    endpoint: str
    method: str
    status_code: int
    duration_ms: int


class ProtocolInfo(TypedDict, total=False):
    """Protocol message information structure."""

    message_id: str
    validation_errors: list[str]
    transport_type: str


class SecurityInfo(TypedDict, total=False):
    """Security event information structure."""

    event_type: str
    user_id: Optional[str]
    ip_address: Optional[str]
    auth_info: Dict[str, Any]


class GatewayLogRecord(logging.LogRecord):
    """Extended LogRecord with additional attributes.

    Adds support for:
    - Metric data
    - API request information
    - Protocol message details
    - Security events
    """

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        # Initialize optional attributes
        self.metric_name: Optional[str] = None
        self.metric_value: Union[int, float, str, None] = None
        self.metric_type: Optional[str] = None
        self.metric_unit: Optional[str] = None
        self.metric_tags: Dict[str, Union[str, int, float]] = {}

        self.request_id: Optional[str] = None
        self.endpoint: Optional[str] = None
        self.method: Optional[str] = None
        self.status_code: Optional[int] = None
        self.duration_ms: Optional[int] = None

        self.message_id: Optional[str] = None
        self.validation_errors: list[str] = []
        self.transport_type: Optional[str] = None

        self.event_type: Optional[str] = None
        self.user_id: Optional[str] = None
        self.ip_address: Optional[str] = None
        self.auth_info: Dict[str, Any] = {}


def create_log_record(
    name: str,
    level: int,
    pathname: str,
    lineno: int,
    msg: str,
    args: tuple,
    exc_info: Optional[tuple],
    func: Optional[str] = None,
    sinfo: Optional[str] = None,
    **kwargs: Any,
) -> GatewayLogRecord:
    """Create a GatewayLogRecord instance.

    Args:
        Standard LogRecord arguments plus additional keyword arguments
        for extended functionality.

    Returns:
        Configured GatewayLogRecord instance
    """
    record = GatewayLogRecord(name, level, pathname, lineno, msg, args, exc_info, func, sinfo)

    # Add any additional attributes from kwargs
    for key, value in kwargs.items():
        setattr(record, key, value)

    return record


# Override the logging.LogRecord factory
logging.setLogRecordFactory(create_log_record)
