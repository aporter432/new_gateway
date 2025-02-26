"""Message field validation according to OGx-1.txt.

This module provides validation for message fields in the OGx protocol.
It ensures that message fields conform to the structure defined in OGx-1.txt.
"""

from typing import Any, Dict, Optional

from Protexis_Command.protocols.ogx.validation.ogx_validation_exceptions import ValidationError
from Protexis_Command.protocols.ogx.validation.validators.ogx_type_validator import (
    ValidationContext,
    ValidationResult,
)


class OGxStructureValidator:
    """Validates message structure according to OGx-1.txt.

    This validator ensures that message fields have the correct structure
    and required properties as defined in the specification.
    """

    def validate(
        self, message: Dict[str, Any], context: Optional[ValidationContext] = None
    ) -> ValidationResult:
        """Validate message structure.

        Args:
            message: Message data to validate
            context: Optional validation context

        Returns:
            ValidationResult indicating if the message is valid

        Raises:
            ValidationError: If message structure is invalid
        """
        if not isinstance(message, dict):
            raise ValidationError("Message must be a dictionary")

        # Validate required fields
        required_fields = {"Name", "SIN", "MIN", "Fields"}
        missing_fields = required_fields - set(message.keys())
        if missing_fields:
            raise ValidationError(f"Missing required fields {', '.join(missing_fields)}")

        # Validate field types
        if not isinstance(message["Name"], str):
            raise ValidationError("Name must be a string")
        if not isinstance(message["SIN"], int):
            raise ValidationError("SIN must be an integer")
        if not isinstance(message["MIN"], int):
            raise ValidationError("MIN must be an integer")
        if not isinstance(message["Fields"], list):
            raise ValidationError("Fields must be a list")

        return ValidationResult(True, [])
