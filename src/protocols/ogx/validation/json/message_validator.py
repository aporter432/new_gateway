"""
OGx message validation according to N214 specification section 5.
Implements message-level validation rules for the Common Message Format.
"""

# Standard library imports
from typing import Any, Dict

# Local imports
from ...constants import (
    REQUIRED_ELEMENT_PROPERTIES,
    REQUIRED_FIELD_PROPERTIES,
    REQUIRED_MESSAGE_FIELDS,
)
from ...exceptions import ValidationError
from .field_validator import OGxFieldValidator

# Third-party imports


class OGxMessageValidator:
    """Validates OGx messages according to N214 specification section 5"""

    def __init__(self) -> None:
        """Initialize the validator with a field validator instance."""
        self.field_validator = OGxFieldValidator()

    def validate_message(self, message: Dict[str, Any]) -> None:
        """
        Validates a complete message structure according to N214 section 5.

        Args:
            message: Dictionary containing the message data

        Raises:
            ValidationError: If message structure is invalid
        """
        # Validate required message fields
        self._validate_required_fields(message, REQUIRED_MESSAGE_FIELDS, "message")

        # Validate message field types and values
        self._validate_message_field_types(message)

        # Validate Fields is a list
        if not isinstance(message["Fields"], list):
            raise ValidationError(
                "Message Fields must be a list", ValidationError.INVALID_MESSAGE_FORMAT
            )

        # Validate each field's required properties first
        for field in message["Fields"]:
            self._validate_field(field)

        # Check for duplicate field names after validating required properties
        field_names = set()
        for field in message["Fields"]:
            if field["Name"] in field_names:
                raise ValidationError(
                    f"Duplicate field name: {field['Name']}", ValidationError.INVALID_MESSAGE_FORMAT
                )
            field_names.add(field["Name"])

        # Validate Name is a string and not empty
        if not isinstance(message["Name"], str):
            raise ValidationError(
                "Message Name must be a string", ValidationError.INVALID_MESSAGE_FORMAT
            )
        if not message["Name"]:
            raise ValidationError(
                "Message Name cannot be empty", ValidationError.INVALID_MESSAGE_FORMAT
            )

    def _validate_field(self, field: Dict[str, Any]) -> None:
        """
        Validates an individual field structure.

        Args:
            field: Dictionary containing the field data

        Raises:
            ValidationError: If field structure is invalid
        """
        # For array fields, Elements is required instead of Value
        if field.get("Type") == "array":
            required_fields = {"Name", "Type", "Elements"}
        else:
            required_fields = REQUIRED_FIELD_PROPERTIES

        # Validate required field properties
        self._validate_required_fields(field, required_fields, "field")

        # Validate field value against its type (skip for array fields)
        if field.get("Type") != "array":
            self.field_validator.validate_field_value(
                field["Type"], field.get("Value"), field.get("TypeAttribute")
            )

        # If field has elements, validate them
        if "Elements" in field:
            if not isinstance(field["Elements"], list):
                raise ValidationError(
                    "Field Elements must be a list", ValidationError.INVALID_FIELD_FORMAT
                )

            for element in field["Elements"]:
                self._validate_element(element)

    def _validate_element(self, element: Dict[str, Any]) -> None:
        """
        Validates an element structure.

        Args:
            element: Dictionary containing the element data

        Raises:
            ValidationError: If element structure is invalid
        """
        # Validate required element properties
        self._validate_required_fields(element, REQUIRED_ELEMENT_PROPERTIES, "element")

        # Validate Index is an integer
        try:
            int(element["Index"])
        except (ValueError, TypeError) as exc:
            raise ValidationError(
                "Element Index must be an integer", ValidationError.INVALID_ELEMENT_FORMAT
            ) from exc

        # Validate Fields is a list
        if not isinstance(element["Fields"], list):
            raise ValidationError(
                "Element Fields must be a list", ValidationError.INVALID_ELEMENT_FORMAT
            )

        # Validate each field in the element
        for field in element["Fields"]:
            self._validate_field(field)

    def _validate_required_fields(
        self, data: Dict[str, Any], required: set[str], context: str
    ) -> None:
        """
        Validates that all required fields are present.

        Args:
            data: Dictionary to validate
            required: Set of required field names
            context: Context for error messages (message/field/element)

        Raises:
            ValidationError: If any required fields are missing
        """
        missing = required - set(data.keys())
        if missing:
            raise ValidationError(
                f"Missing required {context} fields: {', '.join(missing)}",
                ValidationError.MISSING_REQUIRED_FIELD,
            )

    def _validate_message_field_types(self, message: Dict[str, Any]) -> None:
        """
        Validates types of message fields.

        Args:
            message: Message dictionary to validate

        Raises:
            ValidationError: If field types are invalid
        """
        # Validate MIN (Message identification number)
        try:
            min_val = int(message.get("MIN", ""))
            if min_val < 0:
                raise ValueError
        except (TypeError, ValueError) as exc:
            raise ValidationError(
                "MIN must be a non-negative integer", ValidationError.INVALID_FIELD_VALUE
            ) from exc

        # Validate SIN (Service identification number)
        try:
            sin_val = int(message.get("SIN", ""))
            if sin_val < 0:
                raise ValueError
        except (TypeError, ValueError) as exc:
            raise ValidationError(
                "SIN must be a non-negative integer", ValidationError.INVALID_FIELD_VALUE
            ) from exc

        # Validate Name
        if not isinstance(message.get("Name"), str):
            raise ValidationError("Name must be a string", ValidationError.INVALID_FIELD_VALUE)
