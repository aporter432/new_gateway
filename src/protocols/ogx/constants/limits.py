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
"""OGx network payload limit."""

MAX_IDP_SMALL_PAYLOAD_BYTES: Final[int] = 400
"""IDP small message limit."""

MAX_IDP_MEDIUM_PAYLOAD_BYTES: Final[int] = 2000
"""IDP medium message limit."""

MAX_IDP_LARGE_PAYLOAD_BYTES: Final[int] = 10000
"""IDP large message limit."""

MAX_OUTSTANDING_MESSAGES_PER_SIZE: Final[int] = 10
"""Maximum outstanding messages per terminal per size class."""

# Section 2.1.1 - Message Timeout
MESSAGE_TIMEOUT_DAYS: Final[int] = 10
"""Days before closing messages for offline terminals."""

# Default token expiry if not specified
DEFAULT_TOKEN_EXPIRY: Final[timedelta] = timedelta(days=7)
"""Default token expiry if not specified in request."""

ERR_SUBMIT_MESSAGE_RATE_EXCEEDED: Final[int] = 24579
"""Error code when to-mobile message submission rate is exceeded (section 3.4.2.3)."""

ERR_RETRIEVE_STATUS_RATE_EXCEEDED: Final[int] = 24581
"""Error code when to-mobile status retrieval rate is exceeded (section 3.4.2.4)."""
