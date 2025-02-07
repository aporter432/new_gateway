"""Constants for OGx protocol"""

from .field_types import FieldType
from .message_format import (
    REQUIRED_MESSAGE_FIELDS,
    REQUIRED_FIELD_PROPERTIES,
    REQUIRED_ELEMENT_PROPERTIES,
)
from .message_states import MessageState
from .network_types import NetworkType
from .operation_modes import OperationMode
from .auth import AuthRole, ThrottleGroup, GrantType
from .message_types import MessageType
from .transport_types import TransportType
from .endpoints import APIEndpoint
from .limits import (
    MESSAGE_RETENTION_DAYS,
    MAX_SIMULTANEOUS_CONNECTIONS,
    MAX_MESSAGES_PER_RESPONSE,
    MAX_STATUSES_PER_RESPONSE,
    MAX_STATUS_IDS_PER_REQUEST,
    MAX_SUBMIT_MESSAGES,
    DEFAULT_CALLS_PER_MINUTE,
    DEFAULT_WINDOW_SECONDS,
    MAX_CONCURRENT_REQUESTS,
    MAX_TOKEN_EXPIRE_DAYS,
    MAX_OGX_PAYLOAD_BYTES,
    MAX_IDP_SMALL_PAYLOAD_BYTES,
    MAX_IDP_MEDIUM_PAYLOAD_BYTES,
    MAX_IDP_LARGE_PAYLOAD_BYTES,
    MAX_OUTSTANDING_MESSAGES_PER_SIZE,
    MESSAGE_TIMEOUT_DAYS,
    DEFAULT_TOKEN_EXPIRY,
    ERR_SUBMIT_MESSAGE_RATE_EXCEEDED,
    ERR_RETRIEVE_STATUS_RATE_EXCEEDED,
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
    "MAX_IDP_SMALL_PAYLOAD_BYTES",
    "MAX_IDP_MEDIUM_PAYLOAD_BYTES",
    "MAX_IDP_LARGE_PAYLOAD_BYTES",
    "MAX_OUTSTANDING_MESSAGES_PER_SIZE",
    "MESSAGE_TIMEOUT_DAYS",
    "DEFAULT_TOKEN_EXPIRY",
    # Error codes
    "ERR_SUBMIT_MESSAGE_RATE_EXCEEDED",
    "ERR_RETRIEVE_STATUS_RATE_EXCEEDED",
]
