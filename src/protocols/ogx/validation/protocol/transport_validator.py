"""Transport validation according to OGWS-1.txt Section 4.3.1."""

from typing import Any, Dict

from ...constants.transport_types import TransportType
from ..common.base_validator import BaseValidator
from ..common.exceptions import ValidationError
from ..common.types import ValidationContext, ValidationResult


class TransportValidator(BaseValidator):
    """Validates transport types and configurations."""

    def validate(self, data: Dict[str, Any], context: ValidationContext) -> ValidationResult:
        """Validate transport configuration.

        Args:
            data: Transport configuration to validate
            context: Validation context

        Returns:
            ValidationResult with validation status

        Raises:
            ValidationError: If transport configuration is invalid
        """
        self.context = context
        self._errors = []

        try:
            transport = data.get("TransportType")
            if transport not in (
                TransportType.ANY.value,
                TransportType.SATELLITE.value,
                TransportType.CELLULAR.value,
            ):
                raise ValidationError(f"Invalid transport type: {transport}")

            # Validate delayed send options only apply to satellite transport
            if transport == TransportType.CELLULAR.value:
                if data.get("DelayedSendOptions"):
                    raise ValidationError(
                        "Delayed send options not supported for cellular transport"
                    )

            return self._get_validation_result()

        except ValidationError as e:
            self._add_error(str(e))
            return self._get_validation_result()
