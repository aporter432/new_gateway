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

from typing import Any, Dict, Set
from ...constants.error_codes import GatewayErrorCode
from ...constants.field_types import BASIC_TYPE_ATTRIBUTES, FieldType
from ...constants.message_format import (
    REQUIRED_FIELD_PROPERTIES,
    REQUIRED_VALUE_FIELD_PROPERTIES,
)
from ..common.base_validator import BaseValidator
from ..common.exceptions import ValidationError
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

    def validate(self, data: Dict[str, Any], context: ValidationContext) -> ValidationResult:
        """Validate a field's structure and value per OGWS-1.txt Table 3.

        Args:
            data: The field dictionary to validate
            context: Validation context including network type and direction

        Returns:
            ValidationResult indicating if the field is valid and any errors
        """
        self.context = context
        self._errors = []

        try:
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
            result = self.element_validator.validate_array(data["Elements"], self.context)
            if not result.is_valid:
                for error in result.errors:
                    self._add_error(error)

    def _validate_message_field(self, data: Dict[str, Any]) -> None:
        """Validate a message field.

        Args:
            data: The message field data to validate

        Raises:
            ValidationError: If validation fails
        """
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
            raise ValidationError(
                f"Invalid TypeAttribute for {field_type.value} field: {type_attr}",
                GatewayErrorCode.INVALID_FIELD_TYPE,
            )
        self._validate_field_type(FieldType(type_attr.lower()), data.get("Value"))
