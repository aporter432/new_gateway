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

from ..constants.message_types import MessageType
from .fields import MTBPField


@dataclass
class MTBPMessage:
    """Message structure per N210 spec section 3.2"""

    sin: int  # Service ID (1 byte)
    min_id: int  # Message ID (1 byte)
    message_type: MessageType  # Message type (1 byte)
    is_forward: bool  # Direction flag
    fields: List[MTBPField] = field(default_factory=list)  # Message fields
    name: Optional[str] = None  # Optional name for debugging
