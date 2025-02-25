"""Constants for OGx protocol according to OGx-1.txt specification."""

# Import all module components first
from Protexis_Command.protocols.ogx.constants.ogx_field_types import FieldType
from Protexis_Command.protocols.ogx.constants.ogx_limits import (
    DEFAULT_CALLS_PER_MINUTE,
    DEFAULT_TOKEN_EXPIRY,
    DEFAULT_WINDOW_SECONDS,
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
from Protexis_Command.protocols.ogx.constants.ogx_message_format import (
    REQUIRED_ELEMENT_PROPERTIES,
    REQUIRED_FIELD_PROPERTIES,
    REQUIRED_MESSAGE_FIELDS,
)
from Protexis_Command.protocols.ogx.constants.ogx_message_states import MessageState
from Protexis_Command.protocols.ogx.constants.ogx_message_types import MessageType
from Protexis_Command.protocols.ogx.constants.ogx_network_types import NetworkType
from Protexis_Command.protocols.ogx.constants.ogx_operation_modes import OperationMode
from Protexis_Command.protocols.ogx.constants.ogx_transport_types import TransportType

from .http_error_codes import HTTPErrorCode
from .ogx_auth import AuthRole, GrantType, ThrottleGroup
from .ogx_endpoints import APIEndpoint

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
    "HTTPErrorCode",
]
