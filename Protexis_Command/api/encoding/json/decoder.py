"""JSON decoding for OGx message state and metadata.

This module provides consistent JSON decoding across the gateway implementation.
It implements decoding rules as defined in OGx-1.txt specifications.

Configuration Sources:
    - OGx-1.txt Section 5.1: Message Format and Validation
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
    from Protexis_Command.api_ogx.encoding.json import decode_state, decode_message

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

from Protexis_Command.api.config import MessageState
from Protexis_Command.api.validation.format.json.json_validator import OGxJsonValidator
from Protexis_Command.protocols.ogx.models.ogx_messages import OGxMessage
from Protexis_Command.protocols.ogx.validation.ogx_validation_exceptions import EncodingError


class OGxJsonDecoder:
    """OGx protocol message decoder implementing OGx-1.txt specifications."""

    def __init__(self):
        self.validator = OGxJsonValidator()

    def decode(self, data: str) -> Dict[str, Any]:
        """Decode a JSON string to a dictionary following OGx format rules."""
        try:
            decoded = json.loads(data)  # type: ignore # pylint: disable=no-member
            if not isinstance(decoded, dict):
                raise EncodingError("Decoded data must be a JSON object")
            return decoded
        except ValueError as e:  # Catches JSONDecodeError since it's a subclass of ValueError
            raise EncodingError(f"Failed to decode JSON: {str(e)}") from e

    def decode_state(self, data: str) -> Dict[str, Any]:
        """Decode JSON string to message state dictionary."""
        try:
            decoded = json.loads(data)  # type: ignore # pylint: disable=no-member
            if not isinstance(decoded, dict):
                raise EncodingError("State data must be a JSON object")
            state_data = decoded
        except ValueError as e:  # Catches JSONDecodeError since it's a subclass of ValueError
            raise EncodingError("Failed to decode state data") from e

        # Validate required fields
        if "State" not in state_data:
            raise EncodingError("Missing required field: State")
        if "Timestamp" not in state_data:
            raise EncodingError("Missing required field: Timestamp")

        # Validate state value
        try:
            if not isinstance(state_data["State"], MessageState):
                state_data["State"] = MessageState(int(state_data["State"]))
        except (ValueError, TypeError) as e:
            raise EncodingError("Invalid state value") from e

        # Validate timestamp format
        try:
            datetime.fromisoformat(state_data["Timestamp"].replace("Z", "+00:00"))
        except (ValueError, AttributeError) as e:
            raise EncodingError("Invalid timestamp format") from e

        # Validate message format if payload is present
        if "Payload" in state_data:
            try:
                self.validator.validate_message_payload(state_data["Payload"])
            except Exception as e:
                raise EncodingError("Invalid message payload format") from e

        return state_data

    def decode_metadata(self, data: str) -> Dict[str, Any]:
        """Decode JSON string to metadata dictionary."""
        if not data or data == "{}":
            return {}

        try:
            decoded = json.loads(data)  # type: ignore # pylint: disable=no-member
            if not isinstance(decoded, dict):
                raise EncodingError("Metadata must be a JSON object")
            metadata = decoded
        except ValueError as e:
            raise EncodingError("Failed to decode metadata") from e

        # Validate metadata format if it contains message-related fields first
        if any(field in metadata for field in ["Name", "SIN", "MIN", "Fields"]):
            try:
                self.validator.validate_message_payload(metadata)
            except Exception as e:
                raise EncodingError("Invalid message metadata format") from e

        # Then validate metadata values
        for key, value in metadata.items():
            if not isinstance(key, str):
                raise EncodingError(f"Metadata key must be string: {key}")
            if not isinstance(value, (str, int, float, bool, type(None))):
                raise EncodingError(f"Invalid metadata value type for key {key}")

        return metadata

    def decode_message(self, data: Union[str, Dict[str, Any]]) -> OGxMessage:
        """Decode JSON string or dictionary to OGxMessage object."""
        # Convert string to dict if needed
        if isinstance(data, str):
            try:
                message_data = self.decode(data)
            except EncodingError as e:
                raise EncodingError("Failed to decode message data") from e
        else:
            message_data = data.copy()  # Make a copy to avoid modifying the input

        # Validate basic structure
        if not isinstance(message_data, dict):
            raise EncodingError("Message data must be a JSON object")

        # Validate message format
        try:
            self.validator.validate_message_payload(message_data)
        except Exception as e:
            raise EncodingError(f"Invalid message format: {str(e)}") from e

        # Convert to OGxMessage object
        try:
            message = OGxMessage.from_dict(message_data)
            # Create a closure to capture the original data
            original_data = message_data.copy()
            message.to_dict = lambda: original_data  # type: ignore
            return message
        except (TypeError, ValueError, AttributeError) as e:
            raise EncodingError("Failed to create message object") from e


# Create a singleton instance
_decoder = OGxJsonDecoder()

# Export public functions that use the singleton
decode_state = _decoder.decode_state
decode_metadata = _decoder.decode_metadata
decode_message = _decoder.decode_message
