"""Message size validation according to OGWS-1.txt Section 2.1."""

from typing import Any, Dict, Optional

from ...constants.limits import MAX_OGX_PAYLOAD_BYTES
from ...constants.network_types import NetworkType
from ..common.base_validator import BaseValidator
from ..common.validation_exceptions import SizeValidationError  # Changed to use specific exception
from ..common.types import ValidationContext, ValidationResult


class SizeValidator(BaseValidator):
    """Validates message size limits per network type."""

    def __init__(self, message_size_limit: int) -> None:
        """Initialize size validator with maximum message size limit.

        Args:
            message_size_limit: Maximum allowed message size in bytes
        """
        super().__init__()
        self.message_size_limit = message_size_limit

    def validate(
        self, data: Dict[str, Any], context: Optional[ValidationContext]
    ) -> ValidationResult:
        """Validate message size limits.

        Args:
            data: Message data to validate
            context: Optional validation context

        Returns:
            ValidationResult with validation status

        Raises:
            SizeValidationError: If message exceeds size limits
        """
        if not data:
            return ValidationResult(False, ["No data to validate"])

        size = len(str(data))  # Simple size calculation
        if size > self.message_size_limit:
            raise SizeValidationError(
                f"Message size {size} exceeds maximum size {self.message_size_limit}",
                current_size=size,
                max_size=self.message_size_limit,
            )

        return ValidationResult(True, [])
