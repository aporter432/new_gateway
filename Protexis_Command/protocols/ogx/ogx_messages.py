"""Protocol message definitions for OGx Gateway as defined in OGx-1.txt.

This module defines the base message types and structures used in the OGx protocol.
These definitions represent the raw protocol messages before any API-specific serialization.

Implementation Notes from OGx-1.txt:
    - All messages must have a type and version
    - Message types are defined in Section 3.1
    - Message flows are defined in Section 3.2
    - Message validation rules in Section 3.3
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional

from .ogx_fields import ProtocolField


class OGxMessageType(Enum):
    """Message types supported by the OGx protocol."""

    # Authentication messages
    AUTH_REQUEST = "auth_request"
    AUTH_RESPONSE = "auth_response"
    AUTH_ERROR = "auth_error"

    # Device messages
    DEVICE_STATUS = "device_status"
    DEVICE_CONFIG = "device_config"
    DEVICE_ERROR = "device_error"

    # Command messages
    COMMAND_REQUEST = "command_request"
    COMMAND_RESPONSE = "command_response"
    COMMAND_ERROR = "command_error"

    # Event messages
    EVENT_NOTIFICATION = "event_notification"
    EVENT_ACK = "event_ack"
    EVENT_ERROR = "event_error"


class OGxMessageDirection(Enum):
    """Message flow directions in the OGx protocol."""

    GATEWAY_TO_DEVICE = "gateway_to_device"
    DEVICE_TO_GATEWAY = "device_to_gateway"
    BIDIRECTIONAL = "bidirectional"


@dataclass
class OGxMessageFlow:
    """Defines the flow of messages in the OGx protocol."""

    message_type: OGxMessageType
    direction: OGxMessageDirection
    requires_response: bool
    timeout_seconds: int
    retry_count: int


@dataclass
class OGxProtocolMessage:
    """Base class for all OGx protocol messages."""

    message_type: OGxMessageType
    version: str
    message_id: str
    timestamp: int
    fields: Dict[str, ProtocolField]
    flow: OGxMessageFlow

    def validate(self) -> List[str]:
        """Validate message against protocol rules.

        Returns:
            List[str]: List of validation errors, empty if valid
        """
        errors = []

        # Validate required fields
        if not self.message_type:
            errors.append("Message type is required")
        if not self.version:
            errors.append("Version is required")
        if not self.message_id:
            errors.append("Message ID is required")
        if not self.timestamp:
            errors.append("Timestamp is required")

        # Validate field values
        for field_name, field in self.fields.items():
            value = getattr(self, field_name, None)
            if not field.validate(value):
                errors.append(f"Invalid value for field {field_name}")

        return errors


@dataclass
class OGxAuthRequest(OGxProtocolMessage):
    """Authentication request message."""

    username: str
    password: str
    device_id: str
    client_version: str


@dataclass
class OGxAuthResponse(OGxProtocolMessage):
    """Authentication response message."""

    token: str
    expires_at: int
    permissions: List[str]


@dataclass
class OGxCommandRequest(OGxProtocolMessage):
    """Command request message."""

    command: str
    parameters: Dict[str, str]
    target_device: str
    priority: int
    timeout: int


@dataclass
class OGxCommandResponse(OGxProtocolMessage):
    """Command response message."""

    status: str
    result: Optional[Dict[str, str]]
    error_code: Optional[int]
    error_message: Optional[str]


@dataclass
class OGxEventNotification(OGxProtocolMessage):
    """Event notification message."""

    event_type: str
    severity: str
    source: str
    data: Dict[str, str]
    requires_ack: bool
