"""Constants for OGx protocol.

This module serves as the central point for all OGWS protocol constants
as defined in OGWS-1.txt. It provides type-safe enums and constants
for network types, transport types, and various service limits.

The constants defined here should be treated as the source of truth
for the OGWS implementation, ensuring consistency across the codebase.

Spec Compliance:
- All constants align with OGWS-1.txt specifications
- Network types follow section 1.1 definitions
- Transport types implement section 5.4 requirements
- Message limits comply with section 2.3
- Error codes match section 3.4 definitions

Usage:
    from protocols.ogx.constants import (
        NetworkType, TransportType,
        NETWORK_TYPE_OGX, TRANSPORT_TYPE_SATELLITE,
        MAX_OGX_PAYLOAD_BYTES
    )

    # Network type checking
    if network_type == NETWORK_TYPE_OGX:
        # OGx specific handling
        max_size = MAX_OGX_PAYLOAD_BYTES

    # Transport selection
    available_transports = [
        TRANSPORT_TYPE_SATELLITE,
        TRANSPORT_TYPE_CELLULAR
    ]
"""

from enum import Enum, auto

# Import all module components first
from .auth import AuthRole, GrantType, ThrottleGroup
from .endpoints import APIEndpoint
from .field_types import FieldType
from .limits import (
    DEFAULT_CALLS_PER_MINUTE,
    DEFAULT_TOKEN_EXPIRY,
    DEFAULT_WINDOW_SECONDS,
    ERR_RETRIEVE_STATUS_RATE_EXCEEDED,
    ERR_SUBMIT_MESSAGE_RATE_EXCEEDED,
    MAX_CONCURRENT_REQUESTS,
    MAX_MESSAGES_PER_RESPONSE,
    MAX_OGX_PAYLOAD_BYTES,
    MAX_OUTSTANDING_MESSAGES_PER_SIZE,
    MAX_SIMULTANEOUS_CONNECTIONS,
    MAX_STATUS_IDS_PER_REQUEST,
    MAX_STATUSES_PER_RESPONSE,
    MAX_SUBMIT_MESSAGES,
    MAX_TOKEN_EXPIRE_DAYS,
    MESSAGE_RETENTION_DAYS,
    MESSAGE_TIMEOUT_DAYS,
)
from .message_format import (
    REQUIRED_ELEMENT_PROPERTIES,
    REQUIRED_FIELD_PROPERTIES,
    REQUIRED_MESSAGE_FIELDS,
)
from .message_states import MessageState
from .message_types import MessageType
from .network_types import (
    NETWORK_TYPE_OGX,
    NetworkType,
)
from .operation_modes import OperationMode
from .transport_types import (
    TRANSPORT_TYPE_CELLULAR,
    TRANSPORT_TYPE_SATELLITE,
    TransportType,
)

__all__ = [
    "FieldType",
    "REQUIRED_MESSAGE_FIELDS",
    "REQUIRED_FIELD_PROPERTIES",
    "REQUIRED_ELEMENT_PROPERTIES",
    "MessageState",
    "TransportType",
    "NetworkType",
    "OperationMode",
    "MessageType",
    "APIEndpoint",
    # Auth and authorization
    "AuthRole",
    "ThrottleGroup",
    "GrantType",
    # Service limits
    "MESSAGE_RETENTION_DAYS",
    "MAX_SIMULTANEOUS_CONNECTIONS",
    "MAX_MESSAGES_PER_RESPONSE",
    "MAX_STATUSES_PER_RESPONSE",
    "MAX_STATUS_IDS_PER_REQUEST",
    "MAX_SUBMIT_MESSAGES",
    "DEFAULT_CALLS_PER_MINUTE",
    "DEFAULT_WINDOW_SECONDS",
    "MAX_CONCURRENT_REQUESTS",
    "MAX_TOKEN_EXPIRE_DAYS",
    "MAX_OGX_PAYLOAD_BYTES",
    "MAX_OUTSTANDING_MESSAGES_PER_SIZE",
    "MESSAGE_TIMEOUT_DAYS",
    "DEFAULT_TOKEN_EXPIRY",
    # Error codes
    "ERR_SUBMIT_MESSAGE_RATE_EXCEEDED",
    "ERR_RETRIEVE_STATUS_RATE_EXCEEDED",
    "NETWORK_TYPE_OGX",
    "TRANSPORT_TYPE_SATELLITE",
    "TRANSPORT_TYPE_CELLULAR",
]
