"""
MTBP message implementation according to N210 IGWS2 specification section 3.2

Message structure:
- SIN (1 byte): Service Identification Number
- MIN (1 byte): Message Identification Number
- Message Type (1 byte): Type of message (DATA, CONTROL, ACK, NACK)
- Flags (1 byte): Message flags (bit 0 = is_forward)
- Fields (variable): List of message fields
"""

from dataclasses import dataclass, field
from typing import List, Optional

from src.protocols.mtbp.constants.message_types import MessageType
from src.protocols.mtbp.validation.exceptions import ParseError

from .fields import Field


@dataclass
class MTBPMessage:
    """Message structure per N210 spec section 3.2

    Attributes:
        sin: Service ID (1 byte, 0-255)
        min_id: Message ID (1 byte, 0-255)
        message_type: Type of message (DATA, CONTROL, ACK, NACK)
        is_forward: Direction flag (True = to-mobile, False = from-mobile)
        fields: List of message fields
        name: Optional name for debugging
    """

    sin: int  # Service ID (1 byte)
    min_id: int  # Message ID (1 byte)
    message_type: MessageType  # Message type (1 byte)
    is_forward: bool  # Direction flag
    fields: List[Field] = field(default_factory=list)  # Message fields
    name: Optional[str] = None  # Optional name for debugging

    def __post_init__(self):
        """Validate message attributes after initialization"""
        if not isinstance(self.sin, int) or self.sin < 0 or self.sin > 255:
            raise ParseError(
                f"Invalid SIN value: {self.sin}",
                error_code=ParseError.INVALID_SIN,
            )
        if not isinstance(self.min_id, int) or self.min_id < 0 or self.min_id > 255:
            raise ParseError(
                f"Invalid MIN value: {self.min_id}",
                error_code=ParseError.INVALID_MIN,
            )
        if not isinstance(self.message_type, MessageType):
            raise ParseError(
                f"Invalid message type: {self.message_type}",
                error_code=ParseError.INVALID_FIELD_TYPE,
            )
        if not isinstance(self.is_forward, bool):
            raise ParseError(
                f"is_forward must be bool, got {type(self.is_forward)}",
                error_code=ParseError.INVALID_FIELD_VALUE,
            )
        if not isinstance(self.fields, list):
            raise ParseError(
                f"fields must be list, got {type(self.fields)}",
                error_code=ParseError.INVALID_FIELD_VALUE,
            )
        for msg_field in self.fields:
            if not isinstance(msg_field, Field):
                raise ParseError(
                    f"fields must contain Field objects, got {type(msg_field)}",
                    error_code=ParseError.INVALID_FIELD_VALUE,
                )

    def add_field(self, new_field: Field) -> None:
        """Add a field to the message"""
        self.fields.append(new_field)  # __post_init__ will validate on next access

    def get_field(self, index: int) -> Field:
        """Get field at specified index"""
        try:
            return self.fields[index]
        except IndexError as exc:
            raise ParseError(
                f"Field index {index} out of range",
                error_code=ParseError.INVALID_FIELD_VALUE,
            ) from exc

    def clear_fields(self) -> None:
        """Clear all fields from message"""
        self.fields.clear()
