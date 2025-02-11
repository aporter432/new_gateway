"""Field validation according to OGWS-1.txt Section 5.1 Table 3.

This validator implements the field validation rules specified in OGWS-1.txt Section 5.1.
Key validation rules:
- All fields must have Name and Type properties
- Value attribute requirements vary by field type:
  - Basic types (enum, boolean, unsignedint, signedint, string, data) require Value
  - Array type must have Elements instead of Value
  - Message type must have Message instead of Value
  - Dynamic/Property types must have TypeAttribute and Value matching that type
"""

from typing import Any, Dict, Optional, Set
from ...constants.error_codes import GatewayErrorCode
from ...constants.field_types import BASIC_TYPE_ATTRIBUTES, FieldType
from ...constants.message_format import (
    REQUIRED_FIELD_PROPERTIES,
    REQUIRED_VALUE_FIELD_PROPERTIES,
)
from ..common.base_validator import BaseValidator
from ..common.validation_exceptions import ValidationError
from ..common.types import ValidationContext, ValidationResult
from .element_validator import OGxElementValidator


# Field types that require Value attribute per OGWS-1.txt Table 3
VALUE_REQUIRING_TYPES: Set[FieldType] = {
    FieldType.ENUM,
    FieldType.BOOLEAN,
    FieldType.UNSIGNED_INT,
    FieldType.SIGNED_INT,
    FieldType.STRING,
    FieldType.DATA,
}


class OGxFieldValidator(BaseValidator):
    """Validates field values against their declared types per OGWS-1.txt Table 3."""

    def __init__(self) -> None:
        """Initialize with element validator."""
        super().__init__()
        self.element_validator = OGxElementValidator()
        self.context: ValidationContext | None = None

    def validate(
        self, data: Optional[Dict[str, Any]], context: Optional[ValidationContext]
    ) -> ValidationResult:
        """Validate a field's structure and value per OGWS-1.txt Table 3.

        Args:
            data: The field dictionary to validate, or None
            context: Optional validation context

        Returns:
            ValidationResult indicating if the field is valid and any errors
        """
        self.context = context
        self._errors = []

        try:
            # Handle None input data
            if data is None:
                self._add_error(
                    "Required field data missing - Name and Type properties are required"
                )
                return self._get_validation_result()

            # Validate required properties per OGWS-1.txt Section 5.1
            self._validate_required_fields(data, REQUIRED_FIELD_PROPERTIES, "field")

            # Get and validate field type
            field_type = self._validate_and_get_field_type(data)

            # Validate field based on its type
            self._validate_field_by_type(field_type, data)

            return self._get_validation_result()

        except ValidationError as e:
            self._add_error(str(e))
            return self._get_validation_result()

    def _validate_and_get_field_type(self, data: Dict[str, Any]) -> FieldType:
        """Validate and return the field type.

        Args:
            data: The field data containing the Type property

        Returns:
            The validated FieldType enum value

        Raises:
            ValidationError: If the field type is invalid
        """
        field_type_str = data.get("Type", "").lower()
        try:
            return FieldType(field_type_str)
        except ValueError as exc:
            raise ValidationError(
                f"Invalid field type: {field_type_str}", GatewayErrorCode.INVALID_FIELD_TYPE
            ) from exc

    def _validate_field_by_type(self, field_type: FieldType, data: Dict[str, Any]) -> None:
        """Validate field data based on its type.

        Args:
            field_type: The type of the field
            data: The field data to validate

        Raises:
            ValidationError: If validation fails
        """
        if field_type == FieldType.ARRAY:
            self._validate_array_field(data)
        elif field_type == FieldType.MESSAGE:
            self._validate_message_field(data)
        elif field_type in VALUE_REQUIRING_TYPES:
            self._validate_basic_field(field_type, data)
        elif field_type in (FieldType.DYNAMIC, FieldType.PROPERTY):
            self._validate_dynamic_field(field_type, data)

    def _validate_array_field(self, data: Dict[str, Any]) -> None:
        """Validate an array field.

        Args:
            data: The array field data to validate

        Raises:
            ValidationError: If validation fails
        """
        if data.get("Value") is not None:
            raise ValidationError(
                "Array fields must not have Value attribute",
                GatewayErrorCode.INVALID_FIELD_FORMAT,
            )
        if data.get("Elements") is not None:
            if self.context is None:
                raise ValidationError(
                    "Validation context is required for array validation",
                    GatewayErrorCode.INVALID_FIELD_FORMAT,
                )
            # Create a new context with array flag set
            array_context = ValidationContext(
                network_type=self.context.network_type,
                direction=self.context.direction,
                is_array=True,
            )
            result = self.element_validator.validate_array(data["Elements"], array_context)
            if not result.is_valid:
                for error in result.errors:
                    self._add_error(f"In array element: {error}")

    def _validate_message_field(self, data: Dict[str, Any]) -> None:
        """Validate a message field."""
        if data.get("Value") is not None:
            raise ValidationError(
                "Message fields must not have Value attribute",
                GatewayErrorCode.INVALID_FIELD_FORMAT,
            )
        if data.get("Message") is None:
            raise ValidationError(
                "Message fields must have Message attribute",
                GatewayErrorCode.INVALID_FIELD_FORMAT,
            )

        # Check that message content is not empty and has required fields
        message = data.get("Message", {})
        if not message or not isinstance(message, dict):
            self._add_error("Message content must be a non-empty dictionary")
            return

        # Check for required message fields according to OGWS-1.txt Table 3
        required_fields = {"SIN", "MIN", "Fields"}
        missing_fields = [field for field in required_fields if field not in message]
        if missing_fields:
            self._add_error(f"Message content missing required fields: {', '.join(missing_fields)}")
            return

        if self.context is None:
            self._add_error("Validation context is required for message validation")
            return

        # Validate nested message using message validator
        from .message_validator import OGxMessageValidator

        message_validator = OGxMessageValidator()
        result = message_validator.validate(data["Message"], self.context)
        if not result.is_valid:
            for error in result.errors:
                self._add_error(f"In nested message: {error}")

    def _validate_basic_field(self, field_type: FieldType, data: Dict[str, Any]) -> None:
        """Validate a basic field type (enum, boolean, etc.).

        Args:
            field_type: The type of the field
            data: The field data to validate

        Raises:
            ValidationError: If validation fails
        """
        self._validate_required_fields(data, REQUIRED_VALUE_FIELD_PROPERTIES, "field")
        self._validate_field_type(field_type, data.get("Value"))

    def _validate_dynamic_field(self, field_type: FieldType, data: Dict[str, Any]) -> None:
        """Validate a dynamic/property field.

        Args:
            field_type: The type of the field (dynamic or property)
            data: The field data to validate

        Raises:
            ValidationError: If validation fails
        """
        type_attr = data.get("TypeAttribute")
        if not type_attr or type_attr.lower() not in BASIC_TYPE_ATTRIBUTES:
            self._add_error(f"Invalid TypeAttribute for {field_type.value} field: {type_attr}")
            return

        try:
            inner_type = FieldType(type_attr.lower())
            self._validate_field_type(inner_type, data.get("Value"))
        except ValueError:
            self._add_error(f"Invalid TypeAttribute value: {type_attr}")

    def _validate_field_type(self, field_type: FieldType, value: Any) -> None:
        """Validate field value against its type."""
        if field_type == FieldType.UNSIGNED_INT:
            try:
                if value is None:
                    raise ValueError("Value cannot be None")
                int_value = int(value)
                if int_value < 0:
                    self._add_error(
                        f"Invalid value for type {FieldType.UNSIGNED_INT}. Value must be non-negative"
                    )
            except (ValueError, TypeError):
                self._add_error(
                    f"Invalid value for type {FieldType.UNSIGNED_INT}. Value must be a valid integer"
                )
        elif field_type == FieldType.SIGNED_INT:
            try:
                if value is None:
                    raise ValueError("Value cannot be None")
                int(value)  # Just validate it's a valid integer
            except (ValueError, TypeError):
                self._add_error(
                    f"Invalid value for type {FieldType.SIGNED_INT}. Value must be a valid integer"
                )
        elif field_type == FieldType.BOOLEAN:
            if not isinstance(value, bool) and value not in (
                "true",
                "false",
                "True",
                "False",
                "1",
                "0",
            ):
                self._add_error(
                    f"Invalid value for type {FieldType.BOOLEAN}. Value must be a valid boolean"
                )
        elif field_type == FieldType.STRING:
            if not isinstance(value, str):
                self._add_error(
                    f"Invalid value for type {FieldType.STRING}. Value must be a string"
                )
        elif field_type == FieldType.ENUM:
            if not isinstance(value, str) or not value:
                self._add_error(
                    f"Invalid value for type {FieldType.ENUM}. Value must be a non-empty string"
                )
        elif field_type == FieldType.DATA:
            import base64

            if not isinstance(value, str):
                self._add_error(
                    f"Invalid value for type {FieldType.DATA}. Value must be a base64 encoded string"
                )
            else:
                try:
                    # Additional validation for base64 strings
                    if not value or len(value.strip()) % 4 != 0:
                        raise ValueError("Invalid base64 padding")

                    base64.b64decode(value)
                except Exception:
                    self._add_error(
                        f"Invalid value for type {FieldType.DATA}. Value must be a valid base64 encoded string"
                    )
