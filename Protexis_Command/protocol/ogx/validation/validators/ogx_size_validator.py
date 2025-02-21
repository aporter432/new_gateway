"""Size validation for OGx messages.

This module implements size validation rules as defined in OGx-1.txt specifications.
It enforces payload size limits for different message types and network configurations.
"""

from typing import Any, Dict, Optional

from Protexis_Command.protocol.ogx.constants.ogx_limits import MAX_OGX_PAYLOAD_BYTES
from Protexis_Command.protocol.ogx.validation.ogx_validation_exceptions import (
    SizeValidationError,
    ValidationError,
)
from Protexis_Command.protocol.ogx.validation.validators.ogx_base_validator import OGxBaseValidator
from Protexis_Command.protocol.ogx.validation.validators.ogx_type_validator import (
    ValidationContext,
    ValidationResult,
)


class SizeValidator(OGxBaseValidator):
    """Validates message size according to OGx-1.txt."""

    def __init__(self, message_size_limit: int = MAX_OGX_PAYLOAD_BYTES) -> None:
        """Initialize size validator.

        Args:
            message_size_limit: Maximum allowed raw payload size in bytes.
                              Defaults to MAX_OGX_PAYLOAD_BYTES (1023 bytes).
        """
        super().__init__()
        self.message_size_limit = message_size_limit

    def validate(
        self, data: Dict[str, Any], context: Optional[ValidationContext]
    ) -> ValidationResult:
        """Validate message size.

        For RawPayload messages:
            - Validates raw payload is under size limit before Base64 encoding
            - RawPayload takes precedence if both RawPayload and Payload are present
        For JSON messages:
            - Validates message structure follows OGx format
            - Accepts either Payload object or direct Fields array

        Args:
            data: Message data to validate
            context: Optional validation context

        Returns:
            ValidationResult with validation status

        Raises:
            SizeValidationError: If size limits are exceeded
            ValidationError: For other validation errors
        """
        if not data:
            return ValidationResult(False, ["No data to validate"])

        try:
            # Check for required payload first
            if "RawPayload" not in data and "Payload" not in data and "Fields" not in data:
                raise ValidationError("Message must contain either RawPayload or Payload")

            # Check for RawPayload first as it takes precedence
            if "RawPayload" in data:
                raw_payload = data["RawPayload"]
                if not isinstance(raw_payload, str):
                    raise ValidationError("RawPayload must be a string")

                # For RawPayload, check raw size before Base64
                raw_size = len(raw_payload)
                if raw_size > self.message_size_limit:
                    raise SizeValidationError(
                        f"Raw payload size {raw_size} bytes exceeds maximum of {self.message_size_limit} bytes",
                        current_size=raw_size,
                        max_size=self.message_size_limit,
                    )

            # Handle JSON messages (either Payload object or direct Fields)
            elif "Payload" in data:
                if not isinstance(data["Payload"], dict):
                    raise ValidationError("Payload must be a JSON object")
                # No size validation needed for JSON payloads per OGx docs

            # Handle direct Fields array
            elif "Fields" in data:
                if not isinstance(data["Fields"], list):
                    raise ValidationError("Fields must be an array")
                # No size validation needed for Fields per OGx docs

            return ValidationResult(True, [])

        except (TypeError, ValueError, AttributeError) as e:
            self._add_error(f"Failed to validate message: {str(e)}")
            return self._get_validation_result()
