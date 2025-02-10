"""Base validation implementation according to OGWS-1.txt Section 5.

This module provides the foundation for all OGx protocol validation,
implementing the core validation logic defined in the Common Message Format
specification.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from ...constants.field_types import FieldType
from ...constants.message_format import (
    REQUIRED_ELEMENT_PROPERTIES,
    REQUIRED_FIELD_PROPERTIES,
    REQUIRED_MESSAGE_FIELDS,
)
from .exceptions import ValidationError
from .types import ValidationContext, ValidationResult, ValidationType


class BaseValidator(ABC):
    """Base validator implementing OGWS-1.txt Section 5 requirements."""

    def __init__(self) -> None:
        """Initialize the validator."""
        self.context: Optional[ValidationContext] = None
        self._errors: List[str] = []

    @abstractmethod
    def validate(self, data: Any, context: ValidationContext) -> ValidationResult:
        """Perform validation according to OGWS-1.txt specifications.

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
        """Validate required fields presence per OGWS-1.txt Section 5.1.

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
        """Validate field value against its type per OGWS-1.txt Table 3.

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
                    raise ValueError("Boolean value must be true or false")

            elif field_type == FieldType.UNSIGNED_INT:
                int_val = int(float(value)) if isinstance(value, str) else int(value)
                if int_val < 0:
                    raise ValueError("Unsigned integer must be non-negative")

            elif field_type == FieldType.SIGNED_INT:
                int(float(value)) if isinstance(value, str) else int(value)

            elif field_type == FieldType.STRING:
                if not isinstance(value, str):
                    raise ValueError(f"Value must be string, got {type(value).__name__}")

            elif field_type == FieldType.ARRAY:
                if value is not None and not isinstance(value, list):
                    raise ValueError("Array value must be list or None")

            elif field_type == FieldType.MESSAGE:
                if value is not None and not isinstance(value, dict):
                    raise ValueError("Message value must be dictionary or None")

        except (TypeError, ValueError) as exc:
            raise ValidationError(f"Invalid value for type {field_type}: {value}") from exc

    def _add_error(self, message: str) -> None:
        """Add validation error message."""
        self._errors.append(message)

    def _get_validation_result(self) -> ValidationResult:
        """Create validation result from current state."""
        return ValidationResult(
            is_valid=len(self._errors) == 0, errors=self._errors.copy(), context=self.context
        )
