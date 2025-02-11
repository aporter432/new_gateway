"""Message size validation according to OGWS-1.txt.

Key Concepts:
1. Message Types:
   - JSON objects for API calls (with fields like DestinationID, RawPayload, etc.)
   - RawPayload (Base64-encoded) for modem pass-through

2. Size Limits:
   - Raw payload must be under 1023 bytes before Base64 encoding
   - No other size constraints specified in documentation

3. No Low-Level Format:
   - No header structure specified
   - No version bytes or magic numbers
   - No endianness or alignment requirements
"""

from typing import Any, Dict, Optional

from ...constants.limits import MAX_OGX_PAYLOAD_BYTES
from ..common.base_validator import BaseValidator
from ..common.types import ValidationContext, ValidationResult
from ..common.validation_exceptions import SizeValidationError, ValidationError


class SizeValidator(BaseValidator):
    """Validates message size according to OGWS-1.txt."""

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
        For JSON messages:
            - Validates message structure follows OGWS format

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
            # Check if this is a RawPayload message
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

            # For JSON messages, just validate structure
            elif "Payload" in data:
                if not isinstance(data["Payload"], dict):
                    raise ValidationError("Payload must be a JSON object")
                # No size validation needed for JSON payloads per OGWS docs

            else:
                raise ValidationError("Message must contain either RawPayload or Payload")

            return ValidationResult(True, [])

        except (SizeValidationError, ValidationError):
            raise

        except Exception as e:
            self._add_error(f"Failed to validate message: {str(e)}")
            return self._get_validation_result()
