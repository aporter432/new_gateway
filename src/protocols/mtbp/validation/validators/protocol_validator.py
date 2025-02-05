"""
MTBP Protocol Validator

Validates MTBP protocol-level requirements according to N210 IGWS2 specification.
Handles protocol-level validation including:
- Protocol version compatibility
- Message sequencing
- Protocol state transitions
- Transport-specific constraints
"""

from typing import Dict, Optional, Set

from ...constants.message_types import MessageType
from ...models.messages import MTBPMessage
from ..exceptions import ParseError, ProtocolError
from .message_validator import MTBPMessageValidator


class MTBPProtocolValidator:
    """Validates MTBP protocol requirements according to N210 spec"""

    MAX_SEQUENCE_NUMBER = 65535  # 16-bit sequence number
    MAX_OUT_OF_ORDER = 32  # Maximum allowed out-of-order messages

    def __init__(self) -> None:
        """Initialize protocol validator"""
        self._message_validator = MTBPMessageValidator()
        self._last_sequence: Optional[int] = None
        self._seen_sequences: Set[int] = set()  # Track seen sequence numbers
        self._pending_sequences: Dict[int, MTBPMessage] = {}  # Buffer for out-of-order messages
        self._last_message_type: Optional[MessageType] = None  # Track last message type

    def validate(
        self,
        message: MTBPMessage,
        sequence_number: int,
        is_low_power: bool = False,
    ) -> None:
        """
        Validate complete protocol message including:
        - Message structure and content
        - Message sequencing
        - Transport constraints

        Args:
            message: The message to validate
            sequence_number: Sequence number for ordered delivery
            is_low_power: Whether target terminal is in low power mode

        Raises:
            ProtocolError: If protocol-level validation fails
            ParseError: If message validation fails
        """
        try:
            # 1. Validate message structure and content
            self._message_validator.validate(message, is_low_power)

            # 2. Validate sequence number
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
        Validate message sequence number according to N210 spec.

        Handles:
        - Range validation (0-65535)
        - Sequence ordering
        - Out-of-order messages up to MAX_OUT_OF_ORDER
        - Sequence number wrapping
        - Duplicate detection

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

        # Check for duplicates
        if sequence in self._seen_sequences:
            raise ProtocolError(
                f"Duplicate sequence number {sequence}",
                ProtocolError.SEQUENCE_ERROR,
            )

        # If this is the first message, initialize sequence tracking
        if self._last_sequence is None:
            self._last_sequence = sequence
            self._seen_sequences.add(sequence)
            return

        # Calculate expected next sequence with wrapping
        expected = (self._last_sequence + 1) % (self.MAX_SEQUENCE_NUMBER + 1)

        # Handle sequence number wrapping and verify sequence
        if sequence != expected and sequence < self._last_sequence:
            # Allow wrapping only near MAX_SEQUENCE_NUMBER
            if self._last_sequence < self.MAX_SEQUENCE_NUMBER - 1000:
                raise ProtocolError(
                    f"Invalid sequence wrap from {self._last_sequence} "
                    f"to {sequence}, expected {expected}",
                    ProtocolError.SEQUENCE_ERROR,
                )

        # Check if sequence is too far ahead
        if len(self._pending_sequences) >= self.MAX_OUT_OF_ORDER:
            raise ProtocolError(
                f"Too many out-of-order messages (max {self.MAX_OUT_OF_ORDER})",
                ProtocolError.SEQUENCE_ERROR,
            )

        # Update tracking
        self._seen_sequences.add(sequence)
        self._last_sequence = sequence

        # Clean up old sequence numbers
        if len(self._seen_sequences) > self.MAX_OUT_OF_ORDER * 2:
            # Keep only recent sequences
            self._seen_sequences = {
                seq
                for seq in self._seen_sequences
                if abs(seq - self._last_sequence) <= self.MAX_OUT_OF_ORDER
                or (self._last_sequence < 1000 and seq > self.MAX_SEQUENCE_NUMBER - 1000)
            }

    def _validate_message_type_transition(self, message_type: MessageType) -> None:
        """
        Validate message type state transitions.

        Valid transitions:
        - DATA -> ACK/NACK
        - CONTROL -> ACK/NACK
        - ACK -> DATA/CONTROL
        - NACK -> DATA/CONTROL
        - First message can be any type

        Args:
            message_type: Current message type

        Raises:
            ProtocolError: If message type transition is invalid
        """
        if message_type not in MessageType:
            raise ProtocolError(
                f"Invalid message type: {message_type}",
                ProtocolError.PROTOCOL_VIOLATION,
            )

        # First message can be any type
        if self._last_message_type is None:
            self._last_message_type = message_type
            return

        # Check valid transitions
        valid = False
        if self._last_message_type in (MessageType.DATA, MessageType.CONTROL):
            valid = message_type in (MessageType.ACK, MessageType.NACK)
        elif self._last_message_type in (MessageType.ACK, MessageType.NACK):
            valid = message_type in (MessageType.DATA, MessageType.CONTROL)

        if not valid:
            raise ProtocolError(
                f"Invalid message type transition from {self._last_message_type.name} "
                f"to {message_type.name}",
                ProtocolError.PROTOCOL_VIOLATION,
            )

        self._last_message_type = message_type

    def reset_sequence(self) -> None:
        """Reset sequence number tracking (e.g., after connection reset)"""
        self._last_sequence = None
        self._seen_sequences.clear()
        self._pending_sequences.clear()
