"""Message serialization for MTBP protocol.

This module contains the MTBPMessageSerializer class, which handles serializing MTBP messages
to bytes.
"""

import struct

from src.protocols.mtbp.constants.message_types import MessageType
from src.protocols.mtbp.models.messages import MTBPMessage


class MTBPMessageSerializer:
    """Handles MTBP message serialization per N210 spec section 3.1"""

    # SIN, MIN, Sequence, MessageType, Flags, 2 Reserved bytes
    HEADER_FORMAT = "!BBHBBxx"

    @staticmethod
    def to_bytes(message: MTBPMessage) -> bytes:
        """Convert message to bytes according to N210 spec section 3.1"""
        header = struct.pack(
            MTBPMessageSerializer.HEADER_FORMAT,
            message.sin,
            message.min_id,
            message.sequence_number,
            message.message_type.value,
            0x01 if message.is_forward else 0x00,
        )

        field_bytes = b"".join(field.to_bytes() for field in message.fields)
        return header + field_bytes

    @staticmethod
    def from_bytes(data: bytes) -> MTBPMessage:
        """Create message from bytes according to N210 spec section 3.1"""
        if len(data) < struct.calcsize(MTBPMessageSerializer.HEADER_FORMAT):
            raise ValueError("Message too short")

        header_size = struct.calcsize(MTBPMessageSerializer.HEADER_FORMAT)
        sin, min_id, sequence, message_type, flags = struct.unpack(
            MTBPMessageSerializer.HEADER_FORMAT, data[:header_size]
        )

        return MTBPMessage(
            message_type=MessageType(message_type),
            sequence_number=sequence,
            sin=sin,
            min_id=min_id,
            is_forward=bool(flags & 0x01),
            payload=data[header_size:],  # Remaining data
        )
