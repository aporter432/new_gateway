"""
MTBP Message Validator

Validates MTBP messages according to N210 IGWS2 specification sections 3.1 and 3.2.
"""

from ...models.messages import MTBPMessage
from ...validation.exceptions import ParseError
from .field_validator import MTBPFieldValidator
from .header_validator import MTBPHeaderValidator


class MTBPMessageValidator:
    """Validates MTBP messages according to N210 sections 3.1 and 3.2"""

    MAX_MESSAGE_SIZE_REGULAR = 10240  # 10KB limit for regular mode
    MAX_MESSAGE_SIZE_LOW_POWER = 5120  # 5KB limit for low power mode

    def __init__(self) -> None:
        """Initialize validators"""
        self._header_validator = MTBPHeaderValidator()
        self._field_validator = MTBPFieldValidator()

    def validate(self, message: MTBPMessage, is_low_power: bool = False) -> None:
        """
        Validate complete MTBP message structure and content.

        Args:
            message: The message to validate
            is_low_power: Whether target terminal is in low power mode

        Raises:
            ParseError: If message is invalid according to N210 spec
        """
        try:
            # 1. Validate header fields
            self._header_validator.validate(message)

            # 2. Validate message type
            if not message.message_type:
                raise ParseError("Missing message type", ParseError.MISSING_FIELD)

            # 3. Validate fields
            for field in message.fields:
                self._field_validator.validate(field)

            # 4. Validate message size
            self._validate_message_size(message, is_low_power)

        except ParseError:
            raise
        except Exception as e:
            raise ParseError(
                f"Message validation failed: {str(e)}", ParseError.VALIDATION_FAILED
            ) from e

    def _validate_message_size(self, message: MTBPMessage, is_low_power: bool) -> None:
        """
        Validate message size according to N210 section 3.1.

        Args:
            message: The message to validate
            is_low_power: Whether target terminal is in low power mode

        Raises:
            ParseError: If message size exceeds limit
        """
        try:
            # Calculate total size:
            # Header (4 bytes) + Sum of field sizes
            total_size = 4  # SIN(1) + MIN(1) + Type(1) + Flags(1)

            # Add field sizes
            for field in message.fields:
                # Each field: Type(1) + Length(2) + Value
                value_bytes = field.to_bytes()
                total_size += 3 + len(value_bytes)

            # Check against appropriate limit
            max_size = (
                self.MAX_MESSAGE_SIZE_LOW_POWER if is_low_power else self.MAX_MESSAGE_SIZE_REGULAR
            )
            if total_size > max_size:
                raise ParseError(
                    f"Message size {total_size} bytes exceeds {max_size} byte limit",
                    ParseError.INVALID_SIZE,
                )

        except ParseError:
            raise
        except Exception as e:
            raise ParseError(f"Size validation failed: {str(e)}", ParseError.INVALID_SIZE) from e
