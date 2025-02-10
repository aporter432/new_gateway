"""Network validation according to OGWS-1.txt Section 4.2.3."""

from typing import Any, Dict

from ...constants.network_types import NetworkType
from ...constants.operation_modes import OperationMode
from ..common.base_validator import BaseValidator
from ..common.validation_exceptions import ValidationError
from ..common.types import ValidationContext, ValidationResult


class NetworkValidator(BaseValidator):
    """Validates network settings and capabilities."""

    def validate(self, data: Dict[str, Any], context: ValidationContext) -> ValidationResult:
        """Validate network configuration.

        Args:
            data: Network configuration to validate
            context: Validation context

        Returns:
            ValidationResult with validation status

        Raises:
            ValidationError: If network configuration is invalid
        """
        self.context = context
        self._errors = []

        try:
            # Validate network type exists
            network_type = data.get("Network")
            if network_type is None:
                raise ValidationError("Network type is required")

            # Validate against NetworkType enum values
            if network_type != NetworkType.OGX.value:
                raise ValidationError(f"Invalid network type: {network_type}")

            # Validate operation mode per network type
            mode = data.get("OperationMode")
            if mode is not None:
                if network_type == NetworkType.OGX.value:
                    valid_modes = {
                        OperationMode.ALWAYS_ON.value,
                        OperationMode.WAKE_UP.value,
                        OperationMode.MOBILE_RECEIVE_ON_SEND.value,
                        OperationMode.HYBRID.value,
                    }
                    if mode not in valid_modes:
                        raise ValidationError(f"Invalid operation mode {mode} for OGx network")

            return self._get_validation_result()

        except ValidationError as e:
            self._add_error(str(e))
            return self._get_validation_result()
