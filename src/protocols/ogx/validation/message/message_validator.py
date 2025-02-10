"""Message validation according to OGWS-1.txt Section 5.

Implements validation for the Common Message Format as shown in Figure 10:

Message Structure:
- Name (string): Message identifier
- SIN (Service Identification Number, 16-255)
- MIN (Message Identification Number, 1-255)
- IsForward (boolean, optional)
- Fields (array of Field objects)

Implementation Notes:
    This validator ensures:
    1. Required fields presence (Name, SIN, MIN, Fields)
    2. SIN range validation (16-255)
    3. MIN range validation (1-255)
    4. Fields array structure
    5. Individual field validation via OGxFieldValidator
"""

from typing import Any, Dict

from ...constants.error_codes import GatewayErrorCode
from ...constants.message_format import REQUIRED_MESSAGE_FIELDS
from ..common.base_validator import BaseValidator
from ..common.validation_exceptions import ValidationError
from ..common.types import ValidationContext, ValidationResult
from .field_validator import OGxFieldValidator


class OGxMessageValidator(BaseValidator):
    """Validates OGx messages according to OGWS-1.txt Section 5."""

    def __init__(self) -> None:
        """Initialize with field validator."""
        super().__init__()
        self.field_validator = OGxFieldValidator()

    def validate(self, data: Dict[str, Any], context: ValidationContext) -> ValidationResult:
        """Validate message structure and content per OGWS-1.txt Section 5.

        Args:
            data: The message dictionary to validate
            context: Validation context including network type and direction

        Returns:
            ValidationResult indicating if the message is valid and any errors
        """
        self.context = context
        self._errors = []

        try:
            # Validate required fields from Section 5
            self._validate_required_fields(data, REQUIRED_MESSAGE_FIELDS, "message")

            # Validate SIN range (16-255) per Section 5.1
            sin = data.get("SIN")
            if not isinstance(sin, int) or not 16 <= sin <= 255:
                raise ValidationError(
                    f"SIN must be between 16 and 255 (got {sin})",
                    GatewayErrorCode.INVALID_MESSAGE_FORMAT,
                )

            # Validate MIN range (1-255) per Section 5.1
            min_val = data.get("MIN")
            if not isinstance(min_val, int) or not 1 <= min_val <= 255:
                raise ValidationError(
                    f"MIN must be between 1 and 255 (got {min_val})",
                    GatewayErrorCode.INVALID_MESSAGE_FORMAT,
                )

            # Validate Name is a string
            name = data.get("Name")
            if not isinstance(name, str):
                raise ValidationError(
                    "Name must be a string", GatewayErrorCode.INVALID_MESSAGE_FORMAT
                )

            # Validate Fields array structure
            fields = data.get("Fields", [])
            if not isinstance(fields, list):
                raise ValidationError(
                    "Fields must be an array", GatewayErrorCode.INVALID_MESSAGE_FORMAT
                )

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
