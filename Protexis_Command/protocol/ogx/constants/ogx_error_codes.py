"""Protocol-level error codes for OGx Gateway as defined in OGx-1.txt.

This module defines the error codes used in the OGx protocol.
These codes provide detailed error information for gateway operations.

Implementation Notes from OGx-1.txt:
    - Error codes are grouped by category (validation, rate limiting, etc.)
    - Each error has a unique code and message
    - Codes 1000-1999: Message validation errors
    - Codes 2000-2999: Rate limiting and network errors
    - Codes 3000-3999: Message processing errors
"""

from enum import IntEnum


class GatewayErrorCode(IntEnum):
    """Gateway error codes from OGx-1.txt Section 4.2.

    These codes indicate specific error conditions:
    - 0: Success, no error
    - 1xxx: Message validation errors
    - 2xxx: Rate limiting and network errors
    - 3xxx: Message processing errors
    """

    # Success (no error)
    SUCCESS = 0

    # Message Validation Errors (1000-1999)
    INVALID_MESSAGE_TYPE = 1000
    INVALID_MESSAGE_SIZE = 1001
    INVALID_FIELD_VALUE = 1002
    MISSING_REQUIRED_FIELD = 1003
    INVALID_FIELD_LENGTH = 1004
    INVALID_FIELD_FORMAT = 1005
    INVALID_CHECKSUM = 1006
    DUPLICATE_MESSAGE_ID = 1007
    INVALID_SEQUENCE = 1008

    # Rate Limiting and Network Errors (2000-2999)
    RATE_LIMIT_EXCEEDED = 2000
    CONNECTION_ERROR = 2001
    TIMEOUT_ERROR = 2002
    NETWORK_ERROR = 2003
    GATEWAY_UNAVAILABLE = 2004
    SESSION_EXPIRED = 2005

    # Message Processing Errors (3000-3999)
    PROCESSING_ERROR = 3000
    INVALID_TOKEN = 3001
    TOKEN_EXPIRED = 3002
    UNAUTHORIZED_ACCESS = 3003
    DEVICE_NOT_FOUND = 3004
    DEVICE_OFFLINE = 3005
    MESSAGE_QUEUE_FULL = 3006
    INTERNAL_ERROR = 3007
