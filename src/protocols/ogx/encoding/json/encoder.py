"""JSON encoding for OGWS message state and metadata.

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
    from protocols.ogx.encoding.json import encode_state, encode_message

    state_json = encode_state({
        "state": MessageState.ACCEPTED,
        "timestamp": "2024-01-01T00:00:00Z",
        "metadata": {"key": "value"}
    })

    message_json = encode_message(message_obj)
"""

import json
from datetime import datetime
from typing import Any, Dict, Optional, Union

from protocols.ogx.constants import MessageState
from protocols.ogx.exceptions import EncodingError
from protocols.ogx.models.messages import OGxMessage
from protocols.ogx.validation.json.message_validator import OGxMessageValidator


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
            - state: MessageState value
            - timestamp: ISO format timestamp
            - metadata: Optional metadata dictionary

    Returns:
        JSON encoded string

    Raises:
        EncodingError: If encoding fails or data invalid
    """
    validator = OGxMessageValidator()

    # Validate data is a dictionary
    if not isinstance(data, dict):
        raise EncodingError("State data must be a dictionary")

    # Validate required fields
    if "state" not in data:
        raise EncodingError("Missing required field: state")
    if "timestamp" not in data:
        raise EncodingError("Missing required field: timestamp")

    # Validate state value
    try:
        if not isinstance(data["state"], MessageState):
            data["state"] = MessageState(int(data["state"]))
    except (ValueError, TypeError) as e:
        raise EncodingError("Invalid state value") from e

    # Validate timestamp format
    try:
        datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))
    except (ValueError, AttributeError) as e:
        raise EncodingError("Invalid timestamp format") from e

    # Validate payload if present
    if "payload" in data:
        try:
            validator.validate_message(data["payload"])
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
    validator = OGxMessageValidator()

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
            validator.validate_message(metadata)
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
    validator = OGxMessageValidator()

    # Convert OGxMessage to dict if needed
    if isinstance(message, OGxMessage):
        message_data = message.to_dict()
    else:
        message_data = message

    # Validate message format if requested
    if validate:
        try:
            validator.validate_message(message_data)
        except Exception as e:
            raise EncodingError(f"Invalid message format: {str(e)}") from e

    # Encode to JSON
    try:
        return json.dumps(message_data, separators=(",", ":"))
    except TypeError as e:
        raise EncodingError(f"Failed to encode message: {str(e)}") from e
