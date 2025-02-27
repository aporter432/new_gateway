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
from json.decoder import JSONDecodeError
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
            decoded = json.loads(data)
            if not isinstance(decoded, dict):
                raise EncodingError("Decoded data must be a JSON object")
            return decoded
        except JSONDecodeError as e:
            raise EncodingError(f"Failed to decode JSON: {str(e)}") from e

    def decode_state(self, data: str) -> Dict[str, Any]:
        """Decode JSON string to message state dictionary."""
        try:
            state_data = self.decode(data)
        except EncodingError as e:
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
                self.validator.validate_message_payload(state_data["payload"])
            except Exception as e:
                raise EncodingError("Invalid message payload format") from e

        return state_data

    def decode_metadata(self, data: str) -> Dict[str, Any]:
        """Decode JSON string to metadata dictionary."""
        if not data or data == "{}":
            return {}

        try:
            metadata = self.decode(data)
        except EncodingError as e:
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
                self.validator.validate_message_payload(metadata)
            except Exception as e:
                raise EncodingError("Invalid message metadata format") from e

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
            message_data = data

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
            return OGxMessage.from_dict(message_data)
        except Exception as e:
            raise EncodingError(f"Failed to create message object: {str(e)}") from e


# Create a singleton instance
_decoder = OGxJsonDecoder()

# Export public functions that use the singleton
decode_state = _decoder.decode_state
decode_metadata = _decoder.decode_metadata
decode_message = _decoder.decode_message
