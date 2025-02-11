"""Transport validation according to OGWS-1.txt Section 4.3.1."""

from typing import Any, Dict, List, Union

from ...constants.transport_types import TransportType
from ...constants.message_types import MessageType
from ...constants.network_types import NetworkType
from ..common.base_validator import BaseValidator
from ..common.validation_exceptions import ValidationError
from ..common.types import ValidationContext, ValidationResult


class TransportValidator(BaseValidator):
    """Validates transport types according to OGWS-1.txt."""

    def validate(self, data: Dict[str, Any], context: ValidationContext) -> ValidationResult:
        """Validate transport configuration.

        Args:
            data: Transport configuration to validate
            context: Validation context with message direction and network type

        Returns:
            ValidationResult with validation status

        Raises:
            ValidationError: If transport configuration is invalid
        """
        self.context = context
        self._errors = []

        try:
            # 1. First validate message direction
            if not context or not context.direction:
                raise ValidationError("Missing message direction")

            if context.direction not in (MessageType.FORWARD, MessageType.RETURN):
                raise ValidationError(f"Invalid message direction: {context.direction}")

            # 2. Validate network type
            if not context.network_type:
                raise ValidationError("Missing network type in context")

            # Only OGx network is supported in this validator
            if context.network_type.upper() != NetworkType.OGX.name:
                raise ValidationError("Invalid protocol: Expected OGx network")

            # Validate input data
            if data is None:
                raise ValidationError("Invalid data: None")
            if not isinstance(data, dict):
                raise ValidationError("Invalid data type: expected dictionary")

            # 3. Validate transport type
            transport_key = next((k for k in data.keys() if k.lower() == "transport"), None)
            if transport_key is None:
                raise ValidationError("Missing transport type")

            transport = data[transport_key]

            # Handle both single transport and array of transports
            transports = transport if isinstance(transport, list) else [transport]
            for t in transports:
                if not isinstance(t, str):
                    raise ValidationError(f"Invalid transport type: {t}")

                # Convert to uppercase for comparison
                t_upper = t.upper()
                if t_upper not in (TransportType.SATELLITE.name, TransportType.CELLULAR.name):
                    raise ValidationError(f"Invalid transport type: {t}")

            # 4. Validate transport-specific rules
            if any(t.upper() == TransportType.CELLULAR.name for t in transports):
                # Delayed send options not supported for cellular transport
                if data.get("DelayedSendOptions"):
                    raise ValidationError(
                        "Delayed send options not supported for cellular transport"
                    )

            return self._get_validation_result()

        except ValidationError as e:
            self._add_error(str(e))
            return self._get_validation_result()
