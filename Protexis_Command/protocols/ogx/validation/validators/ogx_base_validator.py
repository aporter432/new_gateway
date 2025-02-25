"""Base validation implementation according to OGx-1.txt Section 5.

This module provides the foundation for all OGx protocol validation,
implementing the core validation logic defined in the Common Message Format
specification.

Constants imported here are used by child validator classes:
- REQUIRED_FIELD_PROPERTIES: Field validation (Table 3)
- REQUIRED_MESSAGE_FIELDS: Message validation (Section 5.1)
- REQUIRED_ELEMENT_PROPERTIES: Element validation (Section 5.1)

Child classes should use these constants through the base validator's methods:
- _validate_required_fields(): For field/message/element validation
- _validate_field_type(): For type validation per Table 3
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from Protexis_Command.protocols.ogx.constants.ogx_error_codes import GatewayErrorCode
from Protexis_Command.protocols.ogx.constants.ogx_field_types import FieldType
from Protexis_Command.protocols.ogx.validation.ogx_validation_exceptions import ValidationError
from Protexis_Command.protocols.ogx.validation.validators.ogx_type_validator import (
    ValidationContext,
    ValidationResult,
)


class OGxBaseValidator(ABC):
    """Base validator implementing OGx-1.txt Section 5 requirements."""

    def __init__(self) -> None:
        """Initialize the validator."""
        self.context: Optional[ValidationContext] = None
        self._errors: List[str] = []

    @abstractmethod
    def validate(self, data: Any, context: ValidationContext) -> ValidationResult:
        """Perform validation according to OGx-1.txt specifications.

        Args:
            data: Data to validate
            context: Validation context

        Returns:
            ValidationResult with validation status and any errors

        Raises:
            ValidationError: If validation fails
        """
        raise NotImplementedError

    def _validate_required_fields(
        self, data: Dict[str, Any], required: set[str], context: str
    ) -> None:
        """Validate required fields presence per OGx-1.txt Section 5.1.

        Args:
            data: Dictionary to validate
            required: Set of required field names
            context: Context for error messages

        Raises:
            ValidationError: If required fields are missing
        """
        missing = required - set(data.keys())
        if missing:
            raise ValidationError(f"Missing required {context} fields: {', '.join(missing)}")

    def _validate_field_type(
        self, field_type: FieldType, value: Any, type_attribute: Optional[str] = None
    ) -> None:
        """Validate field value against its type per OGx-1.txt Table 3.

        Args:
            field_type: Field type from FieldType enum
            value: Value to validate
            type_attribute: Type attribute for dynamic/property fields

        Raises:
            ValidationError: If value doesn't match type requirements
        """
        try:
            if field_type in (FieldType.DYNAMIC, FieldType.PROPERTY):
                if not type_attribute:
                    raise ValidationError("Type attribute required for dynamic/property fields")
                # Convert type_attribute to FieldType and validate
                resolved_type = FieldType(type_attribute.lower())
                return self._validate_field_type(resolved_type, value)

            # Implement type-specific validation from Table 3
            if field_type == FieldType.BOOLEAN:
                if not isinstance(value, bool):
                    raise ValidationError(
                        "Invalid boolean field: Value must be a boolean",
                        GatewayErrorCode.INVALID_FIELD_FORMAT,
                    )
                return

            elif field_type == FieldType.UNSIGNED_INT:
                try:
                    int_val = int(float(value)) if isinstance(value, str) else int(value)
                    if int_val < 0:
                        raise ValidationError(
                            "Invalid unsigned integer field: Value must be non-negative",
                            GatewayErrorCode.INVALID_FIELD_FORMAT,
                        )
                except (TypeError, ValueError):
                    raise ValidationError(
                        "Invalid unsigned integer field: Value must be a number",
                        GatewayErrorCode.INVALID_FIELD_FORMAT,
                    )

            elif field_type == FieldType.SIGNED_INT:
                try:
                    int(float(value)) if isinstance(value, str) else int(value)
                except (TypeError, ValueError):
                    raise ValidationError(
                        "Invalid signed integer field: Value must be a number",
                        GatewayErrorCode.INVALID_FIELD_FORMAT,
                    )

            elif field_type == FieldType.STRING:
                if not isinstance(value, str):
                    raise ValidationError(
                        f"Invalid string field: Value must be string, got {type(value).__name__}",
                        GatewayErrorCode.INVALID_FIELD_FORMAT,
                    )

            elif field_type == FieldType.ARRAY:
                if value is not None and not isinstance(value, list):
                    raise ValidationError(
                        "Invalid array field: Value must be list or None",
                        GatewayErrorCode.INVALID_FIELD_FORMAT,
                    )

            elif field_type == FieldType.MESSAGE:
                if value is not None and not isinstance(value, dict):
                    raise ValidationError(
                        "Invalid message field: Value must be dictionary or None",
                        GatewayErrorCode.INVALID_FIELD_FORMAT,
                    )

        except ValidationError:
            raise
        except Exception as exc:
            raise ValidationError(
                f"Invalid {field_type.value} field: {str(exc)}",
                GatewayErrorCode.INVALID_FIELD_FORMAT,
            )

    def _add_error(self, message: str) -> None:
        """Add validation error message."""
        self._errors.append(message)

    def _get_validation_result(self) -> ValidationResult:
        """Create validation result from current state."""
        return ValidationResult(
            is_valid=len(self._errors) == 0, errors=self._errors.copy(), context=self.context
        )
