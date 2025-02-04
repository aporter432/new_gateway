"""Field type definitions per N210 spec"""

from enum import IntEnum

__all__ = ["FieldType"]


class FieldType(IntEnum):
    """Field types as defined in N210 IGWS2 spec section 3.2"""

    STRING = 0x01  # Variable length string
    BOOLEAN = 0x02  # 8-bit boolean
    UINT = 0x03  # Unsigned integer (8, 16, 32, or 64 bits)
    INT = 0x04  # Signed integer (8, 16, 32, or 64 bits)
    ENUM = 0x05  # Enumerated value
    DATA = 0x06  # Binary data
    ARRAY = 0x07  # Array of fields
    MESSAGE = 0x08  # Nested message
    DYNAMIC = 0x09  # Dynamic field
    PROPERTY = 0x0A  # Property field
