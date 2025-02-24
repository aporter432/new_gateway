"""Protocol-level error codes for OGx Gateway as defined in OGx-1.txt.

This module defines the error codes used in the OGx protocol.
These codes provide detailed error information for gateway operations.

Implementation Notes from OGx-1.txt:
    - Base validation errors (10000-10099)
    - Rate limiting errors (24500-24599)
    - Processing errors (26000-26099)
"""

from enum import IntEnum


class GatewayErrorCode(IntEnum):
    """Gateway error codes from OGx-1.txt.

    These codes indicate specific error conditions:
    - 10000-10099: Base validation errors
    - 24500-24599: Rate limiting errors
    - 26000-26099: Processing errors
    """

    # Success (no error)
    SUCCESS = 0

    # Base Validation Errors (10000-10099)
    VALIDATION_ERROR = 10000
    INVALID_MESSAGE_FORMAT = 10001
    INVALID_ELEMENT_FORMAT = 10002
    INVALID_FIELD_FORMAT = 10003
    INVALID_MESSAGE_FILTER = 10004
    MESSAGE_SIZE_EXCEEDED = 10005
    INVALID_FIELD_TYPE = 10006

    # Rate Limiting Errors (24500-24599)
    SUBMIT_MESSAGE_RATE_EXCEEDED = 24579
    RETRIEVE_STATUS_RATE_EXCEEDED = 24581
    INVALID_TOKEN = 24582
    TOKEN_EXPIRED = 24583
    TOKEN_REVOKED = 24584
    TOKEN_INVALID_FORMAT = 24585

    # Processing Errors (26000-26099)
    ENCODE_ERROR = 26000
    DECODE_ERROR = 26001
    PROCESSING_ERROR = 26002
    INTERNAL_ERROR = 26003
