"""Field validation according to OGWS-1.txt Section 5.1 Table 3."""

from typing import Any, Dict

from ...constants.error_codes import GatewayErrorCode
from ...constants.field_types import BASIC_TYPE_ATTRIBUTES, FieldType
from ...constants.message_format import REQUIRED_FIELD_PROPERTIES
from ...models.fields import Field
from ..common.base_validator import BaseValidator
from ..common.exceptions import ValidationError
from ..common.types import ValidationContext, ValidationResult
from .element_validator import OGxElementValidator


class OGxFieldValidator(BaseValidator):
    """Validates field values against their declared types per Table 3."""

    def __init__(self) -> None:
        """Initialize with element validator."""
        super().__init__()
        self.element_validator = OGxElementValidator()

    def validate(self, field: Dict[str, Any], context: ValidationContext) -> ValidationResult:
        """Validate a field's structure and value per OGWS-1.txt Table 3."""
        self.context = context
        self._errors = []

        try:
            # Validate required properties
            self._validate_required_fields(field, REQUIRED_FIELD_PROPERTIES, "field")

            # Get field type
            field_type_str = field.get("Type", "").lower()
            try:
                field_type = FieldType(field_type_str)
            except ValueError:
                raise ValidationError(
                    f"Invalid field type: {field_type_str}", GatewayErrorCode.INVALID_FIELD_TYPE
                )

            # Handle Dynamic/Property fields per Table 3
            if field_type in (FieldType.DYNAMIC, FieldType.PROPERTY):
                type_attr = field.get("TypeAttribute")
                if not type_attr or type_attr.lower() not in BASIC_TYPE_ATTRIBUTES:
                    raise ValidationError(
                        f"Invalid TypeAttribute for {field_type.value} field: {type_attr}",
                        GatewayErrorCode.INVALID_FIELD_TYPE,
                    )
                # Use base validator's field type validation
                self._validate_field_type(FieldType(type_attr.lower()), field.get("Value"))
            else:
                # Use base validator's field type validation
                self._validate_field_type(field_type, field.get("Value"))

            # Validate elements if present
            if field.get("Elements"):
                if field_type != FieldType.ARRAY:
                    raise ValidationError(
                        "Elements only valid for Array type fields",
                        GatewayErrorCode.INVALID_FIELD_FORMAT,
                    )
                for element in field["Elements"]:
                    element_result = self.element_validator.validate(element, context)
                    if not element_result.is_valid:
                        for error in element_result.errors:
                            self._add_error(f"Element validation error: {error}")

            return self._get_validation_result()

        except ValidationError as e:
            self._add_error(str(e))
            return self._get_validation_result()
