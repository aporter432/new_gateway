"""Message size validation according to OGWS-1.txt Section 2.1."""

from typing import Any, Dict

from ...constants.limits import MAX_OGX_PAYLOAD_BYTES
from ...constants.network_types import NetworkType
from ..common.base_validator import BaseValidator
from ..common.validation_exceptions import ValidationError
from ..common.types import ValidationContext, ValidationResult


class SizeValidator(BaseValidator):
    """Validates message size limits per network type."""

    def validate(self, data: Dict[str, Any], context: ValidationContext) -> ValidationResult:
        """Validate message size limits.

        Args:
            data: Message data to validate
            context: Validation context

        Returns:
            ValidationResult with validation status

        Raises:
            ValidationError: If message exceeds size limits
        """
        self.context = context
        self._errors = []

        try:
            payload_size = len(data.get("RawPayload", ""))
            network_type = data.get("Network", NetworkType.OGX.value)

            # Validate OGx network payload limit
            if network_type == NetworkType.OGX.value:
                if payload_size > MAX_OGX_PAYLOAD_BYTES:
                    raise ValidationError(
                        f"OGx payload size {payload_size} exceeds limit of {MAX_OGX_PAYLOAD_BYTES} bytes"
                    )

            return self._get_validation_result()

        except ValidationError as e:
            self._add_error(str(e))
            return self._get_validation_result()
