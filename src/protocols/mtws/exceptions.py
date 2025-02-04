"""MTWS Protocol Exceptions.

This module defines protocol-specific exceptions for the MTWS protocol as specified in N206.
Single Responsibility: Define error types for MTWS protocol violations.
"""

from typing import Optional


class MTWSProtocolError(Exception):
    """Base exception for all MTWS protocol errors."""

    def __init__(self, message: str, error_code: Optional[int] = None):
        self.error_code = error_code
        super().__init__(f"Error {error_code if error_code else 'Unknown'}: {message}")


class MTWSEncodingError(MTWSProtocolError):
    """Encoding errors according to N206 section 2.4.2.

    These errors occur during JSON encoding/decoding operations.
    """

    INVALID_JSON_FORMAT = 201  # JSON syntax or structure invalid
    UNSUPPORTED_ENCODING = 202  # Encoding type not supported (must be JSON/REST)
    DECODE_FAILED = 203  # Unable to decode message content
    ENCODE_FAILED = 204  # Unable to encode message content

    def __init__(self, message: str, error_code: int):
        super().__init__(f"Encoding Error: {message}", error_code)


class MTWSSizeError(MTWSProtocolError):
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

    def __init__(self, message: str, error_code: int, current_size: int, max_size: int):
        self.current_size = current_size
        self.max_size = max_size
        super().__init__(
            f"Size Error: {message} (Current: {current_size} bytes, Max: {max_size} bytes)",
            error_code,
        )


class MTWSFieldError(MTWSProtocolError):
    """Field validation errors according to N206 section 2.4.1.

    These errors relate to field structure and constraints including:
    - Field envelope (2 bytes)
    - Field name requirements
    - Value/Message/Elements constraints
    """

    INVALID_NAME = 401  # Field name missing or invalid
    INVALID_VALUE = 402  # Field value constraint violation
    MULTIPLE_VALUES = 403  # Multiple of Value/Message/Elements present
    MISSING_VALUE = 404  # No Value/Message/Elements present
    INVALID_TYPE = 405  # Field type specification invalid

    def __init__(self, message: str, error_code: int, field_name: Optional[str] = None):
        self.field_name = field_name
        super().__init__(
            f"Field Error: {message}" + (f" in field '{field_name}'" if field_name else ""),
            error_code,
        )


class MTWSElementError(MTWSProtocolError):
    """Element validation errors according to N206 section 2.4.1.

    These errors relate to element structure and constraints including:
    - Elements envelope (16 bytes)
    - Index requirements
    - Fields requirements
    """

    INVALID_INDEX = 501  # Element index invalid or duplicate
    MISSING_FIELDS = 502  # Required Fields array missing
    INVALID_STRUCTURE = 503  # Element structure invalid
    NON_SEQUENTIAL = 504  # Element indices not sequential
    NEGATIVE_INDEX = 505  # Element index is negative

    def __init__(self, message: str, error_code: int, element_index: Optional[int] = None):
        self.element_index = element_index
        super().__init__(
            f"Element Error: {message}"
            + (f" at index {element_index}" if element_index is not None else ""),
            error_code,
        )


class MTWSTransportError(MTWSProtocolError):
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
