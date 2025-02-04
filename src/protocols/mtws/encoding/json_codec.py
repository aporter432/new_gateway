"""MTWS Protocol JSON Codec.

This module provides JSON encoding and decoding for MTWS protocol messages as specified in
N206 section 2.4.2.
Single Responsibility: Encode and decode MTWS protocol messages to/from JSON format.
"""

import json
from typing import Dict

from ..exceptions import MTWSEncodingError
from ..models.messages import CommonMessage
from ..validation.validation import MTWSProtocolValidator


class JSONCodec:
    """Handles JSON encoding and decoding of MTWS protocol messages.

    As defined in N206 section 2.4.2, all MTWS messages must use JSON encoding
    for GPRS web services.
    """

    def __init__(self):
        """Initialize codec with validator"""
        self._validator = MTWSProtocolValidator()

    def encode(self, message: CommonMessage) -> str:
        """Encode a CommonMessage to JSON string according to protocol specification."""
        try:
            # Use existing to_dict method from CommonMessage
            message_dict = message.to_dict()
            encoded = json.dumps(message_dict)
            # Validate protocol constraints
            self._validator.validate_message_size(encoded)
            return encoded
        except (TypeError, ValueError) as e:
            raise MTWSEncodingError(
                f"Failed to encode message: {str(e)}", MTWSEncodingError.ENCODE_FAILED
            ) from e

    def decode(self, json_str: str) -> CommonMessage:
        """Decode a JSON string to CommonMessage according to protocol specification."""
        try:
            # Validate protocol constraints before decoding
            self._validator.validate_message_size(json_str)
            data = json.loads(json_str)
            if not isinstance(data, Dict):
                raise MTWSEncodingError(
                    "JSON data must be an object", MTWSEncodingError.INVALID_JSON_FORMAT
                )
            # Use existing from_dict method from CommonMessage
            return CommonMessage.from_dict(data)
        except json.JSONDecodeError as e:
            raise MTWSEncodingError(
                f"Invalid JSON format: {str(e)}", MTWSEncodingError.INVALID_JSON_FORMAT
            ) from e
