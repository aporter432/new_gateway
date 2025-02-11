"""Network validation according to OGWS-1.txt Section 4.2.3."""

from typing import Any, Dict

from ...constants.message_types import MessageType
from ...constants.network_types import NetworkType
from ..common.base_validator import BaseValidator
from ..common.types import ValidationContext, ValidationResult
from ..common.validation_exceptions import ValidationError


class NetworkValidator(BaseValidator):
    """Validates network settings according to OGWS-1.txt."""

    def validate(self, data: Dict[str, Any], context: ValidationContext) -> ValidationResult:
        """Validate network configuration.

        Args:
            data: Network configuration to validate
            context: Validation context with message direction and network type

        Returns:
            ValidationResult with validation status

        Raises:
            ValidationError: If network configuration is invalid
        """
        self.context = context
        self._errors = []

        try:
            # 1. First validate message direction
            if not context or not context.direction:
                raise ValidationError("Missing message direction")

            if context.direction not in (MessageType.FORWARD, MessageType.RETURN):
                raise ValidationError(f"Invalid message direction: {context.direction}")

            # Validate input data
            if data is None:
                raise ValidationError("Invalid data: None")
            if not isinstance(data, dict):
                raise ValidationError("Invalid data type: expected dictionary")

            # 2. Validate network type
            network_key = next((k for k in data.keys() if k.lower() == "network"), None)
            if network_key is None:
                raise ValidationError("Missing network type")

            network_type = data[network_key]
            if not isinstance(network_type, str):
                raise ValidationError(f"Invalid network type: {network_type}")

            # Only OGx network is supported in this validator
            if network_type.upper() != NetworkType.OGX.name:
                raise ValidationError(f"Invalid network type: {network_type}")

            # 3. Validate network type matches context
            if not context.network_type:
                raise ValidationError("Missing network type in context")

            if context.network_type.upper() != NetworkType.OGX.name:
                raise ValidationError("Invalid network type in context")

            return self._get_validation_result()

        except ValidationError as e:
            self._add_error(str(e))
            return self._get_validation_result()
