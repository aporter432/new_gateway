"""JSON format validator for OGx protocol messages.

Validates JSON message structure and content according to OGx-1.txt specifications.
"""

import json
from datetime import datetime
from typing import Any, Dict, List

from Protexis_Command.api_ogx.constants import MessageState
from Protexis_Command.api_ogx.validation.common.validation_exceptions import ValidationError


class OGxJsonValidator:
    """Validates JSON formatting for OGx messages."""

    # Maximum allowed field lengths
    MAX_STRING_LENGTH = 1024
    MAX_ARRAY_LENGTH = 1000
    MAX_ELEMENTS = 500

    # Allowed field types from OGx spec
    VALID_FIELD_TYPES = {
        "enum",
        "boolean",
        "unsignedint",
        "signedint",
        "string",
        "data",
        "array",
        "message",
    }

    def validate_json_structure(self, data: str) -> None:
        """Validate basic JSON structure.

        Args:
            data: JSON string to validate

        Raises:
            ValidationError: If JSON is malformed
        """
        try:
            if not isinstance(data, str):
                raise ValidationError("Input must be a JSON string")
            json.loads(data)
        except json.JSONDecodeError as e:
            raise ValidationError(f"Invalid JSON format: {str(e)}")

    def validate_message_payload(self, payload: Dict[str, Any]) -> None:
        """Validate message payload structure and content.

        Args:
            payload: Dictionary containing message payload

        Raises:
            ValidationError: If payload format is invalid
        """
        required_fields = {"Name", "SIN", "MIN"}
        if not all(field in payload for field in required_fields):
            raise ValidationError("Message payload missing required fields")

        # Validate SIN and MIN are integers
        if not isinstance(payload["SIN"], int):
            raise ValidationError("SIN must be an integer")
        if not isinstance(payload["MIN"], int):
            raise ValidationError("MIN must be an integer")

        # Validate Name is string and not empty
        if not isinstance(payload["Name"], str) or not payload["Name"].strip():
            raise ValidationError("Name must be a non-empty string")

        # Validate Fields array if present
        if "Fields" in payload:
            self.validate_fields(payload["Fields"])

    def validate_fields(self, fields: List[Dict[str, Any]]) -> None:
        """Validate message fields array.

        Args:
            fields: List of field dictionaries

        Raises:
            ValidationError: If fields format is invalid
        """
        if not isinstance(fields, list):
            raise ValidationError("Fields must be an array")

        if len(fields) > self.MAX_ARRAY_LENGTH:
            raise ValidationError(f"Fields array exceeds maximum length of {self.MAX_ARRAY_LENGTH}")

        for field in fields:
            self.validate_field(field)

    def validate_field(self, field: Dict[str, Any]) -> None:
        """Validate individual message field.

        Args:
            field: Field dictionary to validate

        Raises:
            ValidationError: If field format is invalid
        """
        if not isinstance(field, dict):
            raise ValidationError("Field must be a dictionary")

        # Validate required field properties
        if "Name" not in field:
            raise ValidationError("Field missing required Name property")

        if not isinstance(field["Name"], str) or not field["Name"].strip():
            raise ValidationError("Field Name must be a non-empty string")

        # Validate field type if present
        if "Type" in field:
            if field["Type"] not in self.VALID_FIELD_TYPES:
                raise ValidationError(f"Invalid field type: {field['Type']}")

        # Validate value or elements/message (but not both)
        has_value = "Value" in field
        has_elements = "Elements" in field and field["Elements"] is not None
        has_message = "Message" in field and field["Message"] is not None

        if has_value and (has_elements or has_message):
            raise ValidationError("Field cannot have both Value and Elements/Message")

        if not has_value and not has_elements and not has_message:
            raise ValidationError("Field must have either Value, Elements, or Message")

        # Validate elements if present
        if has_elements:
            self.validate_elements(field["Elements"])

        # Validate embedded message if present
        if has_message:
            self.validate_message_payload(field["Message"])

    def validate_elements(self, elements: List[Dict[str, Any]]) -> None:
        """Validate field elements array.

        Args:
            elements: List of element dictionaries

        Raises:
            ValidationError: If elements format is invalid
        """
        if not isinstance(elements, list):
            raise ValidationError("Elements must be an array")

        if len(elements) > self.MAX_ELEMENTS:
            raise ValidationError(f"Elements array exceeds maximum length of {self.MAX_ELEMENTS}")

        for element in elements:
            if not isinstance(element, dict):
                raise ValidationError("Element must be a dictionary")

            if "Index" not in element:
                raise ValidationError("Element missing required Index")

            if not isinstance(element["Index"], int):
                raise ValidationError("Element Index must be an integer")

            if "Fields" not in element:
                raise ValidationError("Element missing required Fields array")

            self.validate_fields(element["Fields"])

    def validate_state(self, state_data: Dict[str, Any]) -> None:
        """Validate message state data.

        Args:
            state_data: Dictionary containing state information

        Raises:
            ValidationError: If state format is invalid
        """
        required_fields = {"state", "timestamp"}
        if not all(field in state_data for field in required_fields):
            raise ValidationError("State data missing required fields")

        # Validate state value
        try:
            if not isinstance(state_data["state"], MessageState):
                MessageState(int(state_data["state"]))
        except (ValueError, TypeError):
            raise ValidationError("Invalid state value")

        # Validate timestamp format
        try:
            datetime.fromisoformat(state_data["timestamp"].replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            raise ValidationError("Invalid timestamp format")

        # Validate metadata if present
        if "metadata" in state_data:
            self.validate_metadata(state_data["metadata"])

    def validate_metadata(self, metadata: Dict[str, Any]) -> None:
        """Validate message metadata.

        Args:
            metadata: Dictionary containing metadata

        Raises:
            ValidationError: If metadata format is invalid
        """
        if not isinstance(metadata, dict):
            raise ValidationError("Metadata must be a dictionary")

        for key, value in metadata.items():
            if not isinstance(key, str):
                raise ValidationError(f"Metadata key must be string: {key}")

            if not isinstance(value, (str, int, float, bool, type(None))):
                raise ValidationError(f"Invalid metadata value type for key {key}")

            if len(str(key)) > self.MAX_STRING_LENGTH:
                raise ValidationError(f"Metadata key exceeds maximum length: {key}")

            if isinstance(value, str) and len(value) > self.MAX_STRING_LENGTH:
                raise ValidationError(f"Metadata value exceeds maximum length for key: {key}")
