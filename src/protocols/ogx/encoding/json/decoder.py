"""JSON decoding for OGWS message state and metadata.

This module provides consistent JSON decoding across the gateway implementation.
It implements decoding rules as defined in OGWS-1.txt specifications.

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
    from protocols.ogx.encoding.json import decode_state, decode_message

    state_data = decode_state(state_json)
    message_data = decode_message(message_json)
    # Returns:
    # {
    #     "state": MessageState.ACCEPTED,
    #     "timestamp": "2024-01-01T00:00:00Z",
    #     "metadata": {"key": "value"}
    # }
"""

import json
from datetime import datetime
from typing import Any, Dict, Union

from protocols.ogx.constants import MessageState
from protocols.ogx.exceptions import EncodingError
from protocols.ogx.models.messages import OGxMessage
from protocols.ogx.validation.json.message_validator import OGxMessageValidator


class OGxJsonDecoder:
    """JSON decoder for OGx protocol messages."""

    def decode(self, data: str) -> Dict[str, Any]:
        """
        Decode a JSON string to a dictionary.

        Args:
            data: JSON formatted string

        Returns:
            Dict[str, Any]: Decoded dictionary

        Raises:
            EncodingError: If data cannot be decoded to a dictionary
        """
        try:
            decoded = json.loads(data)
            if not isinstance(decoded, dict):
                raise EncodingError("Decoded data must be a JSON object")
            return decoded
        except json.JSONDecodeError as e:
            raise EncodingError(f"Failed to decode JSON: {str(e)}") from e


def decode_state(data: str) -> Dict[str, Any]:
    """Decode JSON string to message state dictionary.

    Implements state decoding as defined in OGWS-1.txt Section 5.1.
    Validates decoded data against message state schema.

    Args:
        data: JSON encoded state string

    Returns:
        Dictionary containing state information:
            - state: MessageState value
            - timestamp: ISO format timestamp
            - metadata: Optional metadata dictionary

    Raises:
        EncodingError: If decoding fails or required fields missing
    """
    validator = OGxMessageValidator()

    try:
        state_data = json.loads(data)
    except json.JSONDecodeError as e:
        raise EncodingError("Failed to decode state data") from e

    if not isinstance(state_data, dict):
        raise EncodingError("State data must be a JSON object")

    # Validate required fields
    if "state" not in state_data:
        raise EncodingError("Missing required field: state")
    if "timestamp" not in state_data:
        raise EncodingError("Missing required field: timestamp")

    # Validate state value
    try:
        state_data["state"] = MessageState(int(state_data["state"]))
    except (ValueError, TypeError) as e:
        raise EncodingError("Invalid state value") from e

    # Validate timestamp format
    try:
        datetime.fromisoformat(state_data["timestamp"].replace("Z", "+00:00"))
    except (ValueError, AttributeError) as e:
        raise EncodingError("Invalid timestamp format") from e

    # Validate message format if payload is present
    if "payload" in state_data:
        try:
            validator.validate_message(state_data["payload"])
        except Exception as e:
            raise EncodingError("Invalid message payload format") from e

    return state_data


def decode_metadata(data: str) -> Dict[str, Any]:
    """Decode JSON string to metadata dictionary.

    Implements metadata decoding as defined in OGWS-1.txt Section 5.1.
    Validates decoded data against metadata schema.

    Args:
        data: JSON encoded metadata string

    Returns:
        Metadata dictionary, empty dict if input is empty/invalid

    Raises:
        EncodingError: If decoding fails or format invalid
    """
    validator = OGxMessageValidator()

    if not data or data == "{}":
        return {}

    try:
        metadata = json.loads(data)
    except json.JSONDecodeError as e:
        raise EncodingError("Failed to decode metadata") from e

    if not isinstance(metadata, dict):
        raise EncodingError("Metadata must be a JSON object")

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

    return metadata


def decode_message(data: Union[str, Dict[str, Any]]) -> OGxMessage:
    """Decode JSON string or dictionary to OGxMessage object.

    Implements message decoding as defined in OGWS-1.txt Section 5.1.
    Validates message data against message schema.

    Args:
        data: JSON encoded message string or dictionary

    Returns:
        OGxMessage object representing the decoded message

    Raises:
        EncodingError: If decoding fails or message format invalid
    """
    validator = OGxMessageValidator()

    # Convert string to dict if needed
    if isinstance(data, str):
        try:
            message_data = json.loads(data)
        except json.JSONDecodeError as e:
            raise EncodingError("Failed to decode message data") from e
    else:
        message_data = data

    # Validate basic structure
    if not isinstance(message_data, dict):
        raise EncodingError("Message data must be a JSON object")

    # Validate message format
    try:
        validator.validate_message(message_data)
    except Exception as e:
        raise EncodingError(f"Invalid message format: {str(e)}") from e

    # Convert to OGxMessage object
    try:
        return OGxMessage.from_dict(message_data)
    except Exception as e:
        raise EncodingError(f"Failed to create message object: {str(e)}") from e
