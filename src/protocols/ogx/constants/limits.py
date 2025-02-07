"""Service limits as defined in N214 sections 2.3, 3.4, and 4.3.

This module defines various limits and thresholds for the OGx Gateway Web Service:

Message Retention and Limitations (Section 2.3):
- Maximum message retention period (5 days)
- Maximum outstanding messages per terminal (10 per size class)
- Maximum messages per response (500)

Access Throttling (Section 3.4):
- Maximum concurrent connections (10 per IP)
- Maximum API calls per minute (5)
- Rate limits by throttle group (INFO/GET/SEND)

Message Size Limits (Section 4.3):
- OGx: 1023 bytes maximum
- IDP Small: 400 bytes maximum
- IDP Medium: 2000 bytes maximum  
- IDP Large: 10000 bytes maximum

Message Timeout (Section 2.1.1):
- Default message timeout: 10 days
- Token expiry: 7 days default, 365 maximum

All constants are marked as Final to prevent modification during runtime.
Values are sourced directly from N214 specification.

Usage:
    from protocols.ogx.constants import (
        MESSAGE_RETENTION_DAYS,
        MAX_MESSAGES_PER_RESPONSE,
        MAX_IDP_MEDIUM_PAYLOAD_BYTES,
        MAX_IDP_LARGE_PAYLOAD_BYTES
    )

    # Check message retention
    def should_purge_message(message_date: datetime) -> bool:
        age_days = (datetime.now() - message_date).days
        return age_days > MESSAGE_RETENTION_DAYS

    # Validate response size
    def validate_response_size(messages: list) -> None:
        if len(messages) > MAX_MESSAGES_PER_RESPONSE:
            raise ValidationError(f"Response exceeds {MAX_MESSAGES_PER_RESPONSE} message limit")

Implementation Notes:
    - Message retention affects storage requirements
    - Size limits are strictly enforced by network
    - Rate limits apply per account and API key
    - Some limits vary by network type
    - Exceeding limits triggers appropriate errors
"""

from datetime import timedelta
from typing import Final


# Section 2.3 - Message Retention and Limitations
MESSAGE_RETENTION_DAYS: Final[int] = 5
"""Messages are retained for 5 days as per N214 section 2.3.

Usage:
    def get_retention_cutoff() -> datetime:
        return datetime.now() - timedelta(days=MESSAGE_RETENTION_DAYS)
"""

MAX_SIMULTANEOUS_CONNECTIONS: Final[int] = 10
"""Maximum simultaneous connections allowed per IP address.

Usage:
    def check_connection_limit(ip: str) -> bool:
        current = get_connection_count(ip)
        return current < MAX_SIMULTANEOUS_CONNECTIONS
"""

MAX_MESSAGES_PER_RESPONSE: Final[int] = 500
"""Maximum messages returned in a single re_messages response.

Usage:
    def paginate_messages(messages: list) -> list[list]:
        return [
            messages[i:i + MAX_MESSAGES_PER_RESPONSE]
            for i in range(0, len(messages), MAX_MESSAGES_PER_RESPONSE)
        ]
"""

MAX_STATUSES_PER_RESPONSE: Final[int] = 500
"""Maximum statuses returned when using timestamp-based queries.

Usage:
    def validate_status_response(statuses: list) -> None:
        if len(statuses) > MAX_STATUSES_PER_RESPONSE:
            raise ValidationError("Too many statuses in response")
"""

MAX_STATUS_IDS_PER_REQUEST: Final[int] = 100
"""Maximum message IDs allowed in fw_statuses request.

Usage:
    def validate_status_request(message_ids: list) -> None:
        if len(message_ids) > MAX_STATUS_IDS_PER_REQUEST:
            raise ValidationError("Too many message IDs in request")
"""

MAX_SUBMIT_MESSAGES: Final[int] = 100
"""Maximum messages allowed in one submit call.

Usage:
    def validate_batch_size(messages: list) -> None:
        if len(messages) > MAX_SUBMIT_MESSAGES:
            raise ValidationError("Batch size exceeds limit")
"""

# Section 3.4 - Access Throttling
DEFAULT_CALLS_PER_MINUTE: Final[int] = 5
"""Default web service call rate per minute.

Usage:
    def check_rate_limit(calls: int) -> bool:
        return calls <= DEFAULT_CALLS_PER_MINUTE
"""

DEFAULT_WINDOW_SECONDS: Final[int] = 60
"""Default sliding window size for rate limiting.

Usage:
    def get_window_start() -> datetime:
        return datetime.now() - timedelta(seconds=DEFAULT_WINDOW_SECONDS)
"""

MAX_CONCURRENT_REQUESTS: Final[int] = 3
"""Maximum parallel requests allowed per account.

Usage:
    def can_process_request(account: str) -> bool:
        active = get_active_requests(account)
        return active < MAX_CONCURRENT_REQUESTS
"""

MAX_TOKEN_EXPIRE_DAYS: Final[int] = 365
"""Maximum allowed token expiry time in days.

Usage:
    def validate_token_expiry(days: int) -> None:
        if days > MAX_TOKEN_EXPIRE_DAYS:
            raise ValidationError("Token expiry exceeds maximum")
"""

# Section 4.3 - Message Size Limits
MAX_OGX_PAYLOAD_BYTES: Final[int] = 1023
"""OGx network message payload limit in bytes.

Usage:
    def validate_ogx_payload(data: bytes) -> None:
        if len(data) > MAX_OGX_PAYLOAD_BYTES:
            raise ValidationError("OGx payload too large")
"""

MAX_IDP_SMALL_PAYLOAD_BYTES: Final[int] = 400
"""IDP small message size limit in bytes.

Usage:
    def is_small_message(size: int) -> bool:
        return size <= MAX_IDP_SMALL_PAYLOAD_BYTES
"""

MAX_IDP_MEDIUM_PAYLOAD_BYTES: Final[int] = 2000
"""IDP medium message size limit in bytes.

Usage:
    def get_message_class(size: int) -> str:
        if size <= MAX_IDP_SMALL_PAYLOAD_BYTES:
            return "SMALL"
        elif size <= MAX_IDP_MEDIUM_PAYLOAD_BYTES:
            return "MEDIUM"
        return "LARGE"
"""

MAX_IDP_LARGE_PAYLOAD_BYTES: Final[int] = 10000
"""IDP large message size limit in bytes.

Usage:
    def validate_idp_payload(data: bytes) -> None:
        if len(data) > MAX_IDP_LARGE_PAYLOAD_BYTES:
            raise ValidationError("IDP payload exceeds maximum size")
"""

MAX_OUTSTANDING_MESSAGES_PER_SIZE: Final[int] = 10
"""Maximum outstanding messages per terminal per size class.

Usage:
    def can_queue_message(terminal: str, size_class: str) -> bool:
        pending = get_pending_count(terminal, size_class)
        return pending < MAX_OUTSTANDING_MESSAGES_PER_SIZE
"""

# Section 2.1.1 - Message Timeout
MESSAGE_TIMEOUT_DAYS: Final[int] = 10
"""Days before closing messages for offline terminals.

Usage:
    def should_timeout_message(message_date: datetime) -> bool:
        age = datetime.now() - message_date
        return age.days >= MESSAGE_TIMEOUT_DAYS
"""

# Default token expiry if not specified
DEFAULT_TOKEN_EXPIRY: Final[timedelta] = timedelta(days=7)
"""Default token expiry period if not specified.

Usage:
    def get_token_expiry(requested_days: int = None) -> datetime:
        if requested_days is None:
            delta = DEFAULT_TOKEN_EXPIRY
        else:
            delta = timedelta(days=min(requested_days, MAX_TOKEN_EXPIRE_DAYS))
        return datetime.now() + delta
"""
