"""
OGx message validation according to N214 specification section 5.
Implements message-level validation rules for the Common Message Format.
"""

# Standard library imports
from typing import Any, Dict, Optional, Union

# Local imports
from ...constants.field_types import FieldType
from ...constants.message_format import (
    REQUIRED_ELEMENT_PROPERTIES,
    REQUIRED_FIELD_PROPERTIES,
    REQUIRED_MESSAGE_FIELDS,
)
from ...exceptions import ValidationError
from ...models.messages import OGxMessage
from .field_validator import OGxFieldValidator

# Third-party imports


class OGxMessageValidator:
    """Validates OGx messages according to OGWS-1.txt specifications."""

    def __init__(self) -> None:
        """Initialize the validator with a field validator instance."""
        self.field_validator = OGxFieldValidator()

    def validate_message(self, message: Union[Dict[str, Any], OGxMessage]) -> Optional[OGxMessage]:
        """
        Validate message format and field values.

        Args:
            message: Dictionary or OGxMessage instance containing message data

        Returns:
            OGxMessage if validation passes

        Raises:
            ValidationError: If message format is invalid
        """
        # Convert OGxMessage to dict if needed
        message_dict: Dict[str, Any]
        if isinstance(message, OGxMessage):
            message_dict = message.to_dict()
        elif isinstance(message, dict):
            message_dict = message
        else:
            raise ValidationError(
                f"Message must be dictionary or OGxMessage, got {type(message)}",
                ValidationError.INVALID_MESSAGE_FORMAT,
            )

        # Validate required message fields
        for field in REQUIRED_MESSAGE_FIELDS:
            if field not in message_dict:
                raise ValidationError(
                    f"Missing required message field: {field}",
                    ValidationError.INVALID_MESSAGE_FORMAT,
                )

        # Validate fields array if present
        fields = message_dict.get("Fields", [])
        if not isinstance(fields, list):
            raise ValidationError("Fields must be an array", ValidationError.INVALID_MESSAGE_FORMAT)

        # Validate each field
        for field in fields:
            if not isinstance(field, dict):
                raise ValidationError(
                    "Field must be an object", ValidationError.INVALID_FIELD_FORMAT
                )

            # Validate required field properties
            for prop in REQUIRED_FIELD_PROPERTIES:
                if prop not in field:
                    raise ValidationError(
                        f"Missing required field property: {prop}",
                        ValidationError.INVALID_FIELD_FORMAT,
                    )

            # Convert field type to FieldType enum
            try:
                field_type = FieldType(field["Type"].lower())
            except (ValueError, AttributeError) as e:
                raise ValidationError(
                    f"Invalid field type: {field.get('Type')}", ValidationError.INVALID_FIELD_TYPE
                ) from e

            # Validate field value using converted FieldType
            self.field_validator.validate_field_value(
                field_type, field.get("Value"), field.get("TypeAttribute")
            )

        # If validation passes, create and return OGxMessage object
        try:
            return OGxMessage.from_dict(message_dict)
        except Exception as e:
            raise ValidationError(
                f"Failed to create message object: {str(e)}", ValidationError.INVALID_MESSAGE_FORMAT
            ) from e

    def _validate_field(self, field: Dict[str, Any]) -> None:
        """
        Validates an individual field structure.

        Args:
            field: Dictionary containing the field data

        Raises:
            ValidationError: If field structure is invalid
        """
        # For array fields, Elements is required instead of Value
        field_type_str = field.get("Type", "").lower()
        try:
            field_type = FieldType(field_type_str)
        except (ValueError, AttributeError) as e:
            raise ValidationError(
                f"Invalid field type: {field_type_str}", ValidationError.INVALID_FIELD_TYPE
            ) from e

        if field_type == FieldType.ARRAY:
            required_fields = {"Name", "Type", "Elements"}
        elif field_type in (FieldType.DYNAMIC, FieldType.PROPERTY):
            required_fields = {"Name", "Type", "Value", "TypeAttribute"}
        else:
            required_fields = REQUIRED_FIELD_PROPERTIES

        # Validate required field properties
        self._validate_required_fields(field, required_fields, "field")

        # Validate field value against its type
        if field_type == FieldType.ARRAY:
            # Validate Elements is a list
            if not isinstance(field.get("Elements"), list):
                raise ValidationError(
                    "Field Elements must be a list", ValidationError.INVALID_FIELD_FORMAT
                )
            # Validate each element
            for element in field["Elements"]:
                self._validate_element(element)
        else:
            # For non-array fields, validate the value
            self.field_validator.validate_field_value(
                field_type, field.get("Value"), field.get("TypeAttribute")
            )

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
            if not isinstance(element["Index"], (int, str)):
                raise ValueError("Element Index must be a number")
            index = int(float(element["Index"]))
            if index < 0:
                raise ValueError("Element Index must be non-negative")
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
