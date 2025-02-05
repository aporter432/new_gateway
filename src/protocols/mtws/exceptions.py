"""MTWS Protocol Exceptions.

This module defines protocol-specific exceptions for the MTWS protocol as specified in N206.
Single Responsibility: Define error types for MTWS protocol violations.
"""

from typing import Optional


class MTWSError(Exception):
    """Base class for MTWS protocol errors."""

    def __init__(self, message: str, error_code: int, **context):
        """Initialize error with message and code."""
        self.error_code = error_code
        self.context = context
        super().__init__(f"Error {error_code}: {message}")


class MTWSEncodingError(MTWSError):
    """Encoding errors according to N206 section 2.4.2.

    These errors occur during JSON encoding/decoding operations.
    """

    INVALID_JSON_FORMAT = 201  # JSON syntax or structure invalid
    UNSUPPORTED_ENCODING = 202  # Encoding type not supported (must be JSON/REST)
    DECODE_FAILED = 203  # Unable to decode message content
    ENCODE_FAILED = 204  # Unable to encode message content

    def __init__(self, message: str, error_code: int):
        super().__init__(f"Encoding Error: {message}", error_code)


class MTWSSizeError(MTWSError):
    """Size validation errors according to N206 section 2.4.3.

    These errors relate to message size constraints including:
    - Message envelope (2 bytes)
    - Message name base (9 bytes)
    - SIN base (7 bytes)
    - MIN base (7 bytes)
    - Fields envelope (12 bytes)
    - HTTP header size (97 bytes + content length)
    - TCP/IP overhead (40 bytes each direction)
    """

    EXCEEDS_MESSAGE_SIZE = 301  # Total message size exceeds 1KB limit
    EXCEEDS_HTTP_HEADER = 302  # HTTP header size violation
    EXCEEDS_GPRS_ROUND = 303  # Exceeds GPRS 1KB rounding
    EXCEEDS_TCP_OVERHEAD = 304  # TCP/IP overhead limit exceeded
    EXCEEDS_FIELD_SIZE = 305  # Field value size exceeds 1KB limit

    def __init__(self, message: str, error_code: int, current_size: int, max_size: int):
        self.current_size = current_size
        self.max_size = max_size
        super().__init__(
            f"Size Error: {message} (Current: {current_size} bytes, Max: {max_size} bytes)",
            error_code,
        )


class MTWSFieldError(MTWSError):
    """Field-related errors in MTWS protocol."""

    INVALID_NAME = 401  # Invalid field name
    INVALID_TYPE = 408  # Invalid field type
    INVALID_LENGTH = 406  # Field length exceeds maximum
    INVALID_VALUE = 405  # Invalid field value
    MISSING_VALUE = 404  # Required field missing
    MULTIPLE_VALUES = 407  # Multiple values provided where only one allowed
    DUPLICATE_NAME = 409  # Duplicate field name

    def __init__(self, message: str, error_code: int, field_name: Optional[str] = None):
        self.field_name = field_name
        super().__init__(
            f"Field Error: {message}" + (f" in field '{field_name}'" if field_name else ""),
            error_code,
        )


class MTWSElementError(MTWSError):
    """Element-related errors."""

    INVALID_INDEX = 500
    MISSING_INDEX = 501
    DUPLICATE_INDEX = 502
    MISSING_FIELDS = 503
    NON_SEQUENTIAL = 504
    NEGATIVE_INDEX = 505
    INVALID_FIELDS = 506
    INVALID_STRUCTURE = 507  # Invalid element structure or format

    def __init__(self, message: str, error_code: int, element_index: Optional[int] = None):
        self.element_index = element_index
        super().__init__(
            f"Element Error: {message}"
            + (f" at index {element_index}" if element_index is not None else ""),
            error_code,
        )


class MTWSTransportError(MTWSError):
    """Transport-related errors according to N206 section 2.3.

    These errors relate to GPRS transport constraints and dual-mode routing.
    """

    INVALID_TRANSPORT = 601  # Invalid transport type
    ROUTING_FAILED = 602  # Dual-mode routing failure
    GPRS_UNAVAILABLE = 603  # GPRS transport unavailable
    SESSION_FAILED = 604  # TCP session failure
    RETRY_EXCEEDED = 605  # Maximum retries exceeded

    def __init__(self, message: str, error_code: int, transport_type: Optional[str] = None):
        self.transport_type = transport_type
        super().__init__(
            f"Transport Error: {message}"
            + (f" for transport '{transport_type}'" if transport_type else ""),
            error_code,
        )
