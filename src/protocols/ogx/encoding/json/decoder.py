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
    from protocols.ogx.encoding.json import decode_state

    state_data = decode_state(state_json)
    # Returns:
    # {
    #     "state": MessageState.ACCEPTED,
    #     "timestamp": "2024-01-01T00:00:00Z",
    #     "metadata": {"key": "value"}
    # }
"""

import json
from datetime import datetime
from typing import Any, Dict

from protocols.ogx.constants import MessageState
from protocols.ogx.exceptions import EncodingError
from protocols.ogx.validation.json.message_validator import OGxMessageValidator


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
