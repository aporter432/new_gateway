"""Constants for OGx protocol"""

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
    MAX_IDP_LARGE_PAYLOAD_BYTES,
    MAX_IDP_MEDIUM_PAYLOAD_BYTES,
    MAX_IDP_SMALL_PAYLOAD_BYTES,
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
from .network_types import NetworkType
from .operation_modes import OperationMode
from .transport_types import TransportType

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
