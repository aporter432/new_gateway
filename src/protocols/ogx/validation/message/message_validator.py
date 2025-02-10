"""Message validation according to OGWS-1.txt Section 5.

Implements validation for the Common Message Format as shown in Figure 10:

Message Structure:
- Name (string)
- SIN (Service Identification Number)
- MIN (Message Identification Number) 
- IsForward (boolean, optional)
- Fields (array of Field objects)
"""

from typing import Any, Dict, List, Optional

from ...constants.message_types import MessageType
from ...constants.message_format import REQUIRED_MESSAGE_FIELDS
from ..common.exceptions import ValidationError
from ..common.base_validator import BaseValidator
from ..common.types import ValidationContext, ValidationResult
from .field_validator import OGxFieldValidator


class OGxMessageValidator(BaseValidator):
    """Validates OGx messages according to OGWS-1.txt Section 5."""

    def __init__(self) -> None:
        """Initialize with field validator."""
        super().__init__()
        self.field_validator = OGxFieldValidator()

    def validate(self, message: Dict[str, Any], context: ValidationContext) -> ValidationResult:
        """Validate message structure and content."""
        self.context = context
        self._errors = []

        try:
            # Validate required fields from Section 5
            self._validate_required_fields(message, REQUIRED_MESSAGE_FIELDS, "message")

            # Validate SIN range (16-255) per Section 5.1
            sin = message.get("SIN")
            if not isinstance(sin, int) or not 16 <= sin <= 255:
                raise ValidationError("SIN must be between 16 and 255")

            # Validate MIN range (1-255) per Section 5.1
            min_val = message.get("MIN")
            if not isinstance(min_val, int) or not 1 <= min_val <= 255:
                raise ValidationError("MIN must be between 1 and 255")

            # Validate Fields array
            fields = message.get("Fields", [])
            if not isinstance(fields, list):
                raise ValidationError("Fields must be an array")

            # Validate each field using field validator
            for field in fields:
                field_result = self.field_validator.validate(field, context)
                if not field_result.is_valid:
                    for error in field_result.errors:
                        self._add_error(f"Field validation error: {error}")

            return self._get_validation_result()

        except ValidationError as e:
            self._add_error(str(e))
            return self._get_validation_result()
