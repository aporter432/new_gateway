"""JSON encoding for OGx message state and metadata.

This module provides consistent JSON encoding across the gateway implementation.
It implements encoding rules as defined in OGWS-1.txt specifications.

Configuration Sources:
    - OGWS-1.txt Section 5.1: Message Format and Validation
    - protocols.ogx.constants: Type definitions and constraints
    - protocols.ogx.validation: Format validation rules

Environment Handling:
    Development:
        - Flexible validation for testing
        - Detailed error messages
        - Debug logging

    Production:
        - Strict validation
        - Sanitized error messages
        - Performance optimization
        - Security constraints

Usage:
    from Protexis_Command.api_ogx.encoding.json import encode_state, encode_message

    state_json = encode_state({
        "State": MessageState.ACCEPTED,
        "Timestamp": "2024-01-01T00:00:00Z",
        "Metadata": {"Key": "Value"}
    })

    message_json = encode_message(message_obj)
"""

import json
from datetime import datetime
from typing import Any, Dict, Optional, Union

from Protexis_Command.api.config import MessageState
from Protexis_Command.api.validation.format.json.json_validator import OGxJsonValidator
from Protexis_Command.protocols.ogx.models.ogx_messages import OGxMessage
from Protexis_Command.protocols.ogx.validation.ogx_validation_exceptions import EncodingError


class OGxJsonEncoder:
    """JSON encoder for OGx protocol messages."""

    def encode(self, obj: Dict[str, Any]) -> str:
        """
        Encode a dictionary to JSON string.

        Args:
            obj: Dictionary to encode

        Returns:
            JSON formatted string
        """
        return json.dumps(obj, default=str)


def encode_state(data: Dict[str, Any]) -> str:
    """Encode message state to JSON string.

    Implements state encoding as defined in OGWS-1.txt Section 5.1.
    Validates state data before encoding.

    Args:
        data: Dictionary containing state information:
            - State: MessageState value
            - Timestamp: ISO format timestamp
            - Metadata: Optional metadata dictionary

    Returns:
        JSON encoded string

    Raises:
        EncodingError: If encoding fails or data invalid
    """
    validator = OGxJsonValidator()

    # Validate data is a dictionary
    if not isinstance(data, dict):
        raise EncodingError("State data must be a dictionary")

    # Validate required fields
    if "State" not in data:
        raise EncodingError("Missing required field: State")
    if "Timestamp" not in data:
        raise EncodingError("Missing required field: Timestamp")

    # Validate state value
    try:
        if not isinstance(data["State"], MessageState):
            data["State"] = MessageState(int(data["State"]))
    except (ValueError, TypeError) as e:
        raise EncodingError("Invalid state value") from e

    # Validate timestamp format
    try:
        datetime.fromisoformat(data["Timestamp"].replace("Z", "+00:00"))
    except (ValueError, AttributeError) as e:
        raise EncodingError("Invalid timestamp format") from e

    # Validate payload if present
    if "Payload" in data:
        try:
            validator.validate_message_payload(data["Payload"])
        except Exception as e:
            raise EncodingError("Invalid message payload format") from e

    # Encode to JSON
    try:
        return json.dumps(data, separators=(",", ":"))
    except TypeError as e:
        raise EncodingError("Failed to encode state data") from e


def encode_metadata(metadata: Optional[Dict[str, Any]] = None) -> str:
    """Encode metadata dictionary to JSON string.

    Implements metadata encoding as defined in OGWS-1.txt Section 5.1.
    Validates metadata before encoding.

    Args:
        metadata: Optional metadata dictionary

    Returns:
        JSON encoded string, '{}' if metadata is None

    Raises:
        EncodingError: If encoding fails or format invalid
    """
    validator = OGxJsonValidator()

    if metadata is None:
        return "{}"

    # Validate metadata is a dictionary
    if not isinstance(metadata, dict):
        raise EncodingError("Metadata must be a dictionary")

    # Validate metadata values
    for key, value in metadata.items():
        if not isinstance(key, str):
            raise EncodingError(f"Metadata key must be string: {key}")
        if not isinstance(value, (str, int, float, bool, type(None))):
            raise EncodingError(f"Invalid metadata value type for key {key}")

    # Validate metadata format if it contains message-related fields
    if any(field in metadata for field in ["Name", "SIN", "MIN", "Fields"]):
        try:
            validator.validate_message_payload(metadata)
        except Exception as e:
            raise EncodingError("Invalid message metadata format") from e

    # Encode to JSON
    try:
        return json.dumps(metadata, separators=(",", ":"))
    except TypeError as e:
        raise EncodingError("Failed to encode metadata") from e


def encode_message(message: Union[OGxMessage, Dict[str, Any]], validate: bool = True) -> str:
    """Encode OGxMessage object or dictionary to JSON string.

    Implements message encoding as defined in OGWS-1.txt Section 5.1.
    Validates message data before encoding if validate=True.

    Args:
        message: OGxMessage object or dictionary to encode
        validate: Whether to validate message before encoding

    Returns:
        JSON encoded string representation of the message

    Raises:
        EncodingError: If encoding fails or message format invalid
    """
    validator = OGxJsonValidator()

    # Convert OGxMessage to dict if needed
    try:
        if hasattr(message, "to_dict"):
            message_data = message.to_dict()
        elif isinstance(message, dict):
            message_data = message
        else:
            raise EncodingError("Message must be either an OGxMessage object or a dictionary")

        # Validate message format if requested
        if validate:
            try:
                validator.validate_message_payload(message_data)
            except Exception as e:
                raise EncodingError(f"Invalid message format: {str(e)}") from e

        # Encode to JSON
        return json.dumps(message_data, separators=(",", ":"))
    except TypeError as e:
        raise EncodingError(f"Failed to encode message: {str(e)}") from e
