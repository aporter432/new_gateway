"""Service limits as defined in OGWS-1.txt sections 2.3, 3.4.

This module defines service limits and thresholds for the OGWS API.

Message Retention and Limitations (from OGWS-1.txt section 2.3):
- Message Retention: 5 days for from-mobile messages
- Firewall Limits: 10 simultaneous connections per IP
- Call Frequency: 5 calls per 60 seconds for GET/INFO/SEND
- Concurrent Requests: Maximum 3 parallel requests per account
- Response Limits:
    - re_messages: 500 messages maximum
    - fw_statuses: 500 statuses (timestamp) or 100 statuses (ID list)
    - fw_messages: 100 messages maximum
    - submit_messages: 100 messages per call

OGWS API Usage Examples:

    # Example 1: Check message retention
    # GET https://ogws.orbcomm.com/api/v1.0/get/re_messages
    from_utc = (
        datetime.now() - timedelta(days=MESSAGE_RETENTION_DAYS)
    ).strftime("%Y-%m-%d %H:%M:%S")
    response = {
        "ErrorID": 0,
        "Messages": [
            {
                "ID": 10844864715,
                "MessageUTC": "2022-11-25 12:00:03",
                "MobileID": "01008988SKY5909"
            }
        ]
    }

    # Example 2: Handle rate limiting
    # HTTP 429 response when exceeding DEFAULT_CALLS_PER_MINUTE
    {
        "ErrorID": 24579,  # ERR_SUBMIT_MESSAGE_RATE_EXCEEDED
        "Message": "Rate limit exceeded. Wait 60 seconds before retrying."
    }

    # Example 3: Submit batch of messages
    # POST https://ogws.orbcomm.com/api/v1.0/submit/messages
    if len(messages) > MAX_SUBMIT_MESSAGES:
        raise ValidationError(f"Cannot submit more than {MAX_SUBMIT_MESSAGES} messages")
    submit_response = {
        "ErrorID": 0,
        "Submissions": [
            {
                "ID": 10844864715,
                "DestinationID": "01008988SKY5909",
                "UserMessageID": 2097
            }
        ]
    }

Implementation Notes from OGWS-1.txt:
    - Message retention affects message availability
    - Rate limits apply per account and throttle group
    - Concurrent request limits prevent overload
    - Response size limits are strictly enforced
    - Some limits configurable via Partner Support
    - HTTP 429 indicates rate limit exceeded
    - HTTP 503 indicates service-wide limits exceeded
    - Token expiry maximum is 365 days
    - Default token expiry is 7 days
"""

from datetime import timedelta
from typing import Final

# Section 2.3 - Message Retention and Limitations
MESSAGE_RETENTION_DAYS: Final[int] = 5
"""From-mobile messages are retained for 5 days."""

MAX_SIMULTANEOUS_CONNECTIONS: Final[int] = 10
"""Maximum simultaneous connections per IP address."""

MAX_MESSAGES_PER_RESPONSE: Final[int] = 500
"""Maximum messages in re_messages response."""

MAX_STATUSES_PER_RESPONSE: Final[int] = 500
"""Maximum statuses when using timestamp-based queries."""

MAX_STATUS_IDS_PER_REQUEST: Final[int] = 100
"""Maximum message IDs in fw_statuses request."""

MAX_SUBMIT_MESSAGES: Final[int] = 100
"""Maximum messages per submit call."""

# Section 3.4 - Access Throttling
DEFAULT_CALLS_PER_MINUTE: Final[int] = 5
"""Default API calls per minute per throttle group."""

DEFAULT_WINDOW_SECONDS: Final[int] = 60
"""Default sliding window for rate limiting."""

MAX_CONCURRENT_REQUESTS: Final[int] = 3
"""Maximum parallel requests per account."""

MAX_TOKEN_EXPIRE_DAYS: Final[int] = 365
"""Maximum allowed token expiry in days."""

# Section 4.3 - Message Size Limits
MAX_OGX_PAYLOAD_BYTES: Final[int] = 1023
"""OGx network raw payload limit in bytes."""

MAX_OUTSTANDING_MESSAGES_PER_SIZE: Final[int] = 10
"""Maximum outstanding messages per terminal."""

# Section 2.1.1 - Message Timeout
MESSAGE_TIMEOUT_DAYS: Final[int] = 10
"""Days before closing messages for offline terminals."""

# Default token expiry if not specified
DEFAULT_TOKEN_EXPIRY: Final[timedelta] = timedelta(days=365)
"""Default token expiry if not specified in request."""


# Helper functions for size calculations
def calculate_base64_size(binary_size: int) -> int:
    """Calculate size after Base64 encoding.

    Args:
        binary_size: Size of raw binary data

    Returns:
        Size after Base64 encoding (includes padding)
    """
    # Base64 encoding: 3 bytes -> 4 chars
    # Plus padding to nearest 4 chars
    return ((binary_size + 2) // 3) * 4


def calculate_json_overhead(base64_size: int) -> int:
    """Calculate approximate JSON wrapper overhead.

    Args:
        base64_size: Size of Base64 encoded string

    Returns:
        Approximate size of complete JSON message
    """
    # Rough estimate including:
    # - JSON field names and syntax
    # - Base64 string
    # - Other required fields
    json_overhead = 50  # Minimum JSON structure overhead
    return base64_size + json_overhead


def validate_payload_size(binary_size: int) -> bool:
    """Validate raw binary payload size.

    Args:
        binary_size: Size of raw binary data

    Returns:
        True if size is within limits
    """
    return binary_size <= MAX_OGX_PAYLOAD_BYTES
