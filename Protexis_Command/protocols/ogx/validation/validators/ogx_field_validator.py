"""Field validator for OGx protocol.

This module implements field validation for OGx protocol messages.
"""

import base64
from typing import Any, Dict, Optional, Set

from ...constants.ogx_error_codes import GatewayErrorCode
from ...constants.ogx_field_types import BASIC_TYPE_ATTRIBUTES, FieldType
from ...constants.ogx_message_format import (
    REQUIRED_FIELD_PROPERTIES,
    REQUIRED_VALUE_FIELD_PROPERTIES,
)
from ..ogx_validation_exceptions import ValidationError
from .ogx_base_validator import OGxBaseValidator
from .ogx_element_validator import OGxElementValidator
from .ogx_structure_validator import OGxStructureValidator
from .ogx_type_validator import ValidationContext, ValidationResult

# Field types that require Value attribute per OGx-1.txt Table 3
VALUE_REQUIRING_TYPES: Set[FieldType] = {
    FieldType.ENUM,
    FieldType.BOOLEAN,
    FieldType.UNSIGNED_INT,
    FieldType.SIGNED_INT,
    FieldType.STRING,
    FieldType.DATA,
}


class OGxFieldValidator(OGxBaseValidator):
    """Validates field values against their declared types per OGx-1.txt Table 3."""

    def __init__(self) -> None:
        """Initialize with element validator."""
        super().__init__()
        self.element_validator = OGxElementValidator()
        self.context: ValidationContext | None = None

    def validate(
        self, data: Optional[Dict[str, Any]], context: Optional[ValidationContext]
    ) -> ValidationResult:
        """Validate a field's structure and value per OGx-1.txt Table 3.

        Args:
            data: The field dictionary to validate, or None
            context: Optional validation context

        Returns:
            ValidationResult indicating if the field is valid and any errors

        Raises:
            ValidationError: If validation fails with critical errors
        """
        self.context = context
        self._errors = []

        try:
            # Handle None input data
            if data is None:
                raise ValidationError(
                    "Required field data missing - Name and Type properties are required"
                )

            # Validate required properties per OGx-1.txt Section 5.1
            self._validate_required_fields(data, REQUIRED_FIELD_PROPERTIES, "field")

            # Get and validate field type
            field_type = self._validate_and_get_field_type(data)

            # Validate field based on its type
            if field_type == FieldType.MESSAGE:
                return self.validate_message_field(data, context)
            else:
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
        elif field_type in VALUE_REQUIRING_TYPES:
            self._validate_basic_field(field_type, data)
        elif field_type in (FieldType.DYNAMIC, FieldType.PROPERTY):
            self._validate_dynamic_field(field_type, data)

    def _validate_array_field(self, data: Dict[str, Any]) -> None:
        """Validate an array field according to OGx-1.txt Table 3.

        According to the specification:
        - Array fields must NOT have a Value attribute
        - Elements is optional
        - When Elements is present:
            - Must be a list
            - Each element must have Index and Fields
            - Fields must be a list
            - Index must be sequential starting from 0
            - No duplicate indices allowed

        Args:
            data: The array field data to validate

        Raises:
            ValidationError: If validation fails with critical errors
        """
        # Array fields should not have Value attribute at all
        if "Value" in data:
            raise ValidationError(
                "Invalid array field: Value attribute not allowed",
                GatewayErrorCode.INVALID_FIELD_FORMAT,
            )

        # Elements is optional for array fields
        if "Elements" in data:
            elements = data["Elements"]
            if not isinstance(elements, list):
                raise ValidationError(
                    "Invalid array field: Elements must be a list",
                    GatewayErrorCode.INVALID_FIELD_FORMAT,
                )

            # Track indices for sequential and duplicate validation
            seen_indices = set()
            expected_index = 0

            for idx, element in enumerate(elements):
                if not isinstance(element, dict):
                    raise ValidationError(
                        f"Invalid array element at index {idx}: Must be a dictionary",
                        GatewayErrorCode.INVALID_FIELD_FORMAT,
                    )

                if "Index" not in element:
                    raise ValidationError(
                        f"Invalid array element at index {idx}: Missing required field Index",
                        GatewayErrorCode.INVALID_FIELD_FORMAT,
                    )

                element_index = element["Index"]
                if not isinstance(element_index, int):
                    raise ValidationError(
                        f"Invalid array element at index {idx}: Index must be an integer",
                        GatewayErrorCode.INVALID_FIELD_FORMAT,
                    )

                # Check for sequential indices starting at 0
                if element_index != expected_index:
                    raise ValidationError(
                        f"Invalid array element at index {idx}: Index must be {expected_index}",
                        GatewayErrorCode.INVALID_FIELD_FORMAT,
                    )

                # Check for duplicate indices
                if element_index in seen_indices:
                    raise ValidationError(
                        f"Invalid array element at index {idx}: Duplicate index {element_index}",
                        GatewayErrorCode.INVALID_FIELD_FORMAT,
                    )
                seen_indices.add(element_index)
                expected_index += 1

                if "Fields" not in element:
                    raise ValidationError(
                        f"Invalid array element at index {idx}: Missing required field Fields",
                        GatewayErrorCode.INVALID_FIELD_FORMAT,
                    )

                fields = element["Fields"]
                if not isinstance(fields, list):
                    raise ValidationError(
                        f"Invalid array element at index {idx}: Fields must be a list",
                        GatewayErrorCode.INVALID_FIELD_FORMAT,
                    )

                # Validate each field in the element
                for field in fields:
                    try:
                        result = self.validate(field, self.context)
                        if not result.is_valid:
                            # Add each error with array element context
                            for error in result.errors:
                                self._add_error(f"In array element {idx}: {error}")
                            raise ValidationError(
                                f"In array element {idx}: {result.errors[0]}",
                                GatewayErrorCode.INVALID_FIELD_FORMAT,
                            )
                    except ValidationError as e:
                        # Add error with array element context
                        error_msg = f"In array element {idx}: {str(e)}"
                        self._add_error(error_msg)
                        raise ValidationError(
                            error_msg,
                            GatewayErrorCode.INVALID_FIELD_FORMAT,
                        ) from e

    def validate_message_field(
        self, field: Dict[str, Any], context: Optional[ValidationContext]
    ) -> ValidationResult:
        """Validate a message field.

        Args:
            field: Field data to validate
            context: Validation context

        Returns:
            ValidationResult indicating if the field is valid
        """
        try:
            # Validate context
            if not context:
                raise ValidationError("Validation context required")

            # Value attribute not allowed for message fields per OGWS-1.txt Table 3
            if "Value" in field:
                raise ValidationError("Value attribute not allowed for message fields")

            # Validate Message attribute exists and is a dictionary
            message = field.get("Message")
            if not message:
                raise ValidationError("Missing required field Message")
            if not isinstance(message, dict):
                raise ValidationError("Message must be a non-empty dictionary")

            # Validate required message fields per OGWS-1.txt Section 5.1
            required_fields = {"SIN", "MIN", "Fields"}
            missing_fields = required_fields - set(message.keys())
            if missing_fields:
                raise ValidationError(
                    f"Missing required fields: {', '.join(sorted(missing_fields))}"
                )

            # Validate SIN and MIN are integers
            sin = message.get("SIN")
            if not isinstance(sin, int):
                raise ValidationError("SIN must be an integer")

            min_val = message.get("MIN")
            if not isinstance(min_val, int):
                raise ValidationError("MIN must be an integer")

            # Validate Fields is a list
            fields = message.get("Fields")
            if not isinstance(fields, list):
                raise ValidationError("Fields must be a list")

            # Validate message structure using OGxStructureValidator
            try:
                validator = OGxStructureValidator()
                result = validator.validate(message, context)
                if not result.is_valid:
                    raise ValidationError(f"Message validation failed: {result.errors[0]}")
            except ImportError as e:
                raise ValidationError(f"Message validation unavailable: {str(e)}")

            return self._get_validation_result()

        except ValidationError as e:
            self._add_error(str(e))
            return self._get_validation_result()
        except Exception as e:
            self._add_error(f"Unexpected error validating message field: {str(e)}")
            return self._get_validation_result()

    def _validate_basic_field(self, field_type: FieldType, data: Dict[str, Any]) -> None:
        """Validate a basic field type (enum, boolean, etc.).

        Args:
            field_type: The type of the field
            data: The field data to validate

        Raises:
            ValidationError: If validation fails
        """
        self._validate_required_fields(data, REQUIRED_VALUE_FIELD_PROPERTIES, "field")
        value = data.get("Value")
        if value is None:
            raise ValidationError(
                f"Invalid {field_type.value} field: Missing required value",
                GatewayErrorCode.INVALID_FIELD_FORMAT,
            )
        self._validate_field_type(field_type, value)

    def _validate_dynamic_field(self, field_type: FieldType, data: Dict[str, Any]) -> None:
        """Validate a dynamic/property field.

        Args:
            field_type: The type of the field (dynamic or property)
            data: The field data to validate

        Raises:
            ValidationError: If validation fails with critical errors
        """
        self._validate_required_fields(data, REQUIRED_VALUE_FIELD_PROPERTIES, "field")

        type_attr = data.get("TypeAttribute")
        if not type_attr:
            raise ValidationError(
                f"Invalid {field_type.value} field: Missing required field TypeAttribute",
                GatewayErrorCode.INVALID_FIELD_FORMAT,
            )

        if type_attr.lower() not in BASIC_TYPE_ATTRIBUTES:
            raise ValidationError(
                f"Invalid {field_type.value} field: TypeAttribute {type_attr} not allowed",
                GatewayErrorCode.INVALID_FIELD_FORMAT,
            )

        try:
            inner_type = FieldType(type_attr.lower())
            value = data.get("Value")
            # Validate type first, then check for null
            self._validate_field_type(inner_type, value, check_null=False)
            if value is None:
                raise ValidationError(
                    f"Invalid {field_type.value} field: Missing required value",
                    GatewayErrorCode.INVALID_FIELD_FORMAT,
                )
        except ValueError as exc:
            raise ValidationError(
                f"Invalid {field_type.value} field: Invalid TypeAttribute {type_attr}",
                GatewayErrorCode.INVALID_FIELD_FORMAT,
            ) from exc

    def _validate_field_type(
        self,
        field_type: FieldType,
        value: Any,
        type_attribute: Optional[str] = None,
        check_null: bool = True,
    ) -> None:
        """Validate field value against its type.

        Args:
            field_type: The type of the field
            value: The value to validate
            type_attribute: Optional type attribute for dynamic fields
            check_null: Whether to check for null values first

        Raises:
            ValidationError: If validation fails with an invalid value
        """
        if check_null and value is None:
            raise ValidationError(
                f"Invalid {field_type.value} field: Missing required value",
                GatewayErrorCode.INVALID_FIELD_FORMAT,
            )

        try:
            if field_type == FieldType.UNSIGNED_INT:
                try:
                    int_value = int(value)
                    if int_value < 0:
                        raise ValidationError(
                            f"Invalid {field_type.value} field: Value must be non-negative",
                            GatewayErrorCode.INVALID_FIELD_FORMAT,
                        )
                except (ValueError, TypeError) as exc:
                    raise ValidationError(
                        f"Invalid {field_type.value} field: Value must be an integer",
                        GatewayErrorCode.INVALID_FIELD_FORMAT,
                    ) from exc

            elif field_type == FieldType.SIGNED_INT:
                try:
                    int(float(value)) if isinstance(value, str) else int(value)
                except (ValueError, TypeError) as exc:
                    raise ValidationError(
                        f"Invalid {field_type.value} field: Value must be an integer",
                        GatewayErrorCode.INVALID_FIELD_FORMAT,
                    ) from exc

            elif field_type == FieldType.BOOLEAN:
                valid_bool_strings = ("true", "false", "True", "False", "1", "0")
                if not isinstance(value, bool) and str(value) not in valid_bool_strings:
                    raise ValidationError(
                        f"Invalid {field_type.value} field: Value must be a boolean",
                        GatewayErrorCode.INVALID_FIELD_FORMAT,
                    )

            elif field_type == FieldType.STRING:
                if not isinstance(value, str):
                    raise ValidationError(
                        f"Invalid {field_type.value} field: Value must be a string",
                        GatewayErrorCode.INVALID_FIELD_FORMAT,
                    )

            elif field_type == FieldType.ENUM:
                if not isinstance(value, str) or not value:
                    raise ValidationError(
                        f"Invalid {field_type.value} field: Value must be a non-empty string",
                        GatewayErrorCode.INVALID_FIELD_FORMAT,
                    )

            elif field_type == FieldType.DATA:
                if not isinstance(value, str):
                    raise ValidationError(
                        f"Invalid {field_type.value} field: Value must be a valid base64",
                        GatewayErrorCode.INVALID_FIELD_FORMAT,
                    )
                try:
                    # Empty string is valid base64
                    if not value:
                        return

                    # Additional validation for base64 strings
                    if len(value.strip()) % 4 != 0:
                        raise ValueError("Invalid base64 padding")

                    base64.b64decode(value)
                except Exception as exc:
                    raise ValidationError(
                        f"Invalid {field_type.value} field: Value must be a valid base64 encoded string",
                        GatewayErrorCode.INVALID_FIELD_FORMAT,
                    ) from exc

        except ValidationError:
            raise
        except Exception as exc:
            raise ValidationError(
                f"Invalid {field_type.value} field: Unexpected error {str(exc)}",
                GatewayErrorCode.INVALID_FIELD_FORMAT,
            ) from exc

    def validate_field_type(
        self,
        field_type: FieldType,
        value: Any,
        type_attribute: Optional[str] = None,
        check_null: bool = True,
    ) -> None:
        """Validate a field value against its declared type.

        Public interface for field type validation, following OGx-1.txt Table 3 rules.

        Args:
            field_type: The type to validate against
            value: The value to validate
            type_attribute: Optional type attribute for dynamic fields
            check_null: Whether to check for null values

        Raises:
            ValidationError: If the value doesn't match type requirements
        """
        return self._validate_field_type(field_type, value, type_attribute, check_null)

    def validate_terminal_id(self, terminal_id: str) -> None:
        """Validate terminal ID format per OGx-1.txt Section 5.1.2.

        Args:
            terminal_id: Terminal ID to validate

        Raises:
            ValidationError: If terminal ID format is invalid
        """
        if not terminal_id or not isinstance(terminal_id, str):
            raise ValidationError("Terminal ID must be a non-empty string")

        if not terminal_id.isalnum():
            raise ValidationError("Terminal ID must contain only alphanumeric characters")

        if len(terminal_id) < 8 or len(terminal_id) > 20:
            raise ValidationError("Terminal ID must be between 8 and 20 characters")
