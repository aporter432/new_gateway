"""Network validation according to OGx-1.txt Section 4.2.3."""

from typing import Any, Dict

from ...constants.ogx_message_types import MessageType
from ...constants.ogx_network_types import NetworkType
from ..ogx_validation_exceptions import ValidationError
from .ogx_base_validator import OGxBaseValidator
from .ogx_type_validator import ValidationContext, ValidationResult


class NetworkValidator(OGxBaseValidator):
    """Validates network settings according to OGx-1.txt."""

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

            # Convert string network type to enum if needed
            if isinstance(network_type, str):
                try:
                    network_type = NetworkType(int(network_type))
                except (ValueError, TypeError):
                    raise ValidationError(f"Invalid network type value: {network_type}")
            elif not isinstance(network_type, NetworkType):
                raise ValidationError(f"Invalid network type: {network_type}")

            # Only OGx network is supported in this validator
            if network_type != NetworkType.OGX:
                raise ValidationError(f"Invalid network type: {network_type}")

            # 3. Validate network type matches context
            if not context.network_type:
                raise ValidationError("Missing network type in context")

            if not isinstance(context.network_type, NetworkType):
                raise ValidationError("Invalid network type in context")

            if context.network_type != NetworkType.OGX:
                raise ValidationError(f"Invalid network type in context: {context.network_type}")

            return self._get_validation_result()

        except ValidationError as e:
            self._add_error(str(e))
            return self._get_validation_result()
