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
        return json.dumps(obj, default=str)  # type: ignore # pylint: disable=no-member


class OGWSJsonEncoder:
    """Custom JSON encoder that handles OGWS-specific encoding requirements."""

    def encode(self, obj: Any) -> str:
        """Encode an object to JSON string, raising EncodingError for invalid data."""
        try:
            return json.dumps(obj, default=str)  # type: ignore # pylint: disable=no-member
        except UnicodeError as e:
            raise EncodingError("Failed to encode metadata") from e


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

    if not isinstance(metadata, dict):
        raise EncodingError("Metadata must be a dictionary")

    # Validate top-level structure if it resembles a message
    if any(key in metadata for key in ["Name", "SIN", "MIN", "Fields"]):
        try:
            validator.validate_message_payload(metadata)
        except Exception as e:
            raise EncodingError("Invalid message metadata format") from e

    def validate_value(value: Any, allow_nesting: bool = False) -> None:
        """Validate a metadata value recursively."""
        if isinstance(value, dict):
            if not allow_nesting:
                raise EncodingError("Invalid metadata value type")
            if "Name" in value or "Fields" in value:
                try:
                    validator.validate_message_payload(value)
                except Exception as e:
                    raise EncodingError("Invalid message metadata format") from e
            else:
                raise EncodingError("Invalid metadata value type")  # Reject non-message dicts
        elif isinstance(value, str):
            try:
                value.encode("utf-8").decode("utf-8")
            except UnicodeError:
                raise EncodingError("Failed to encode metadata")
        elif not isinstance(value, (int, float, bool, type(None))):
            raise EncodingError("Invalid metadata value type")  # Reject non-primitive types

    # Validate keys are strings and nested values
    for key in metadata:
        if not isinstance(key, str):
            raise EncodingError(f"Metadata key must be string: {key}")
    for value in metadata.values():
        validate_value(value, allow_nesting=True)

    # Try to encode, raising a generic error for serialization failures
    try:
        return json.dumps(metadata, separators=(",", ":"), ensure_ascii=True)
    except (TypeError, ValueError, UnicodeError) as e:
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
        if isinstance(message, dict):
            message_data = message
        elif hasattr(message, "to_dict") and callable(message.to_dict):  # type: ignore
            message_data = message.to_dict()  # type: ignore
        else:
            raise EncodingError(
                f"Message must be either an OGxMessage object or a dictionary: {type(message)}"
            )

        # Validate message format if requested
        if validate:
            try:
                validator.validate_message_payload(message_data)
            except Exception as e:
                raise EncodingError(f"Invalid message format: {str(e)}") from e

        # Encode to JSON
        return json.dumps(message_data, separators=(",", ":"))  # type: ignore # pylint: disable=no-member
    except TypeError as e:
        raise EncodingError(f"Failed to encode message: {str(e)}") from e
