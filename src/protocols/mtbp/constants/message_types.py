"""MTBP message type definitions per N210 spec"""

from enum import IntEnum


class MessageType(IntEnum):
    """MTBP message types per N210 spec section 3.1"""

    DATA = 0x01
    CONTROL = 0x02
    ACK = 0x03
    NACK = 0x04
