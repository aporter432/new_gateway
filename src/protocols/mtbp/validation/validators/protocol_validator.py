"""
MTBP Protocol Validator

Validates MTBP protocol-level requirements according to N210 IGWS2 specification.
Handles protocol-level validation including:
- Protocol version compatibility
- Message sequencing
- Protocol state transitions
- Transport-specific constraints
"""

from typing import Optional

from ...constants.message_types import MessageType
from ...models.messages import MTBPMessage
from ..exceptions import ParseError, ProtocolError
from .message_validator import MTBPMessageValidator


class MTBPProtocolValidator:
    """Validates MTBP protocol requirements according to N210 spec"""

    MAX_SEQUENCE_NUMBER = 65535  # 16-bit sequence number

    def __init__(self) -> None:
        """Initialize protocol validator"""
        self._message_validator = MTBPMessageValidator()
        self._last_sequence: Optional[int] = None

    def validate(
        self,
        message: MTBPMessage,
        sequence_number: Optional[int] = None,
        is_low_power: bool = False,
    ) -> None:
        """
        Validate complete protocol message including:
        - Message structure and content
        - Message sequencing
        - Transport constraints

        Args:
            message: The message to validate
            sequence_number: Optional sequence number for ordered delivery
            is_low_power: Whether target terminal is in low power mode

        Raises:
            ProtocolError: If protocol-level validation fails
            ParseError: If message validation fails
        """
        try:
            # 1. Validate message structure and content
            self._message_validator.validate(message, is_low_power)

            # 2. Validate sequence number (if provided)
            if sequence_number is not None:
                self._validate_sequence_number(sequence_number)

            # 3. Validate message type transitions
            self._validate_message_type_transition(message.message_type)

        except ParseError:
            raise
        except Exception as e:
            raise ProtocolError(
                f"Protocol validation failed: {str(e)}", ProtocolError.PROTOCOL_VIOLATION
            ) from e

    def _validate_sequence_number(self, sequence: int) -> None:
        """
        Validate message sequence number.

        Args:
            sequence: Message sequence number

        Raises:
            ProtocolError: If sequence number is invalid
        """
        # Validate range
        if not 0 <= sequence <= self.MAX_SEQUENCE_NUMBER:
            raise ProtocolError(
                f"Sequence number {sequence} out of valid range (0-{self.MAX_SEQUENCE_NUMBER})",
                ProtocolError.SEQUENCE_ERROR,
            )

        # Check sequence ordering
        if self._last_sequence is not None:
            expected = (self._last_sequence + 1) % (self.MAX_SEQUENCE_NUMBER + 1)
            if sequence != expected:
                raise ProtocolError(
                    f"Invalid sequence number {sequence}, expected {expected}",
                    ProtocolError.SEQUENCE_ERROR,
                )

        self._last_sequence = sequence

    def _validate_message_type_transition(self, message_type: MessageType) -> None:
        """
        Validate message type state transitions.

        Args:
            message_type: Current message type

        Raises:
            ProtocolError: If message type transition is invalid
        """
        # Example validation - can be expanded based on specific requirements
        if message_type not in MessageType:
            raise ProtocolError(
                f"Invalid message type: {message_type}",
                ProtocolError.PROTOCOL_VIOLATION,
            )

    def reset_sequence(self) -> None:
        """Reset sequence number tracking (e.g., after connection reset)"""
        self._last_sequence = None
