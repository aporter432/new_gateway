"""Constants for the OGx protocol."""

from .ogx_error_codes import GatewayErrorCode
from .ogx_field_types import FieldType
from .ogx_limits import (
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
    calculate_base64_size,
    calculate_json_overhead,
    validate_payload_size,
)
from .ogx_message_format import (
    REQUIRED_ELEMENT_PROPERTIES,
    REQUIRED_FIELD_PROPERTIES,
    REQUIRED_MESSAGE_FIELDS,
    REQUIRED_VALUE_FIELD_PROPERTIES,
)
from .ogx_message_states import MessageState
from .ogx_message_types import MessageType
from .ogx_network_types import NETWORK_TYPE_OGX, NetworkType
from .ogx_operation_modes import OperationMode
from .ogx_transport_types import TransportType

__all__ = [
    "FieldType",
    "calculate_base64_size",
    "calculate_json_overhead",
    "validate_payload_size",
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
    "calculate_base64_size",
    "calculate_json_overhead",
    "validate_payload_size",
    "REQUIRED_MESSAGE_FIELDS",
    "REQUIRED_FIELD_PROPERTIES",
    "REQUIRED_VALUE_FIELD_PROPERTIES",
    "REQUIRED_ELEMENT_PROPERTIES",
    "MessageState",
    "MessageType",
    "NetworkType",
    "NETWORK_TYPE_OGX",
    "OperationMode",
    "TransportType",
    "GatewayErrorCode",
]
