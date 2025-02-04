"""
MTBP Fields Model and Serialization (N210 Spec Section 3.2)

This module defines the FieldType enum and provides methods for serializing and deserializing
MTBP fields according to the N210 specification.
"""

import struct
from dataclasses import dataclass
from typing import Union

from src.protocols.mtbp.constants.field_types import FieldType
from src.protocols.mtbp.validation.exceptions import ParseError


class FieldSize:
    """Defines the fixed byte sizes for different field types."""

    UINT = 4  # 32-bit unsigned integer
    INT = 4  # 32-bit signed integer
    BOOLEAN = 1  # 1 byte for boolean values


@dataclass
class Field:
    """Represents a field in an MTBP message, supporting serialization and deserialization."""

    field_type: FieldType
    value: Union[str, int, bool, bytes]

    def to_bytes(self) -> bytes:
        """Convert field value to bytes according to N210 spec section 3.2"""
        try:
            if self.field_type == FieldType.STRING:
                if not isinstance(self.value, str):
                    raise ParseError(
                        "String field must have str value", ParseError.INVALID_FIELD_VALUE
                    )
                encoded_value = self.value.encode("utf-8")
                return struct.pack(f"!H{len(encoded_value)}s", len(encoded_value), encoded_value)

            elif self.field_type == FieldType.BOOLEAN:
                if not isinstance(self.value, bool):
                    raise ParseError(
                        "Boolean field must have bool value", ParseError.INVALID_FIELD_VALUE
                    )
                return struct.pack("!B", 1 if self.value else 0)

            elif self.field_type in (FieldType.UINT, FieldType.INT, FieldType.ENUM):
                if not isinstance(self.value, int):
                    raise ParseError(
                        f"{self.field_type.name} field must have int value",
                        ParseError.INVALID_FIELD_VALUE,
                    )
                if self.field_type == FieldType.UINT and self.value < 0:
                    raise ParseError(
                        "UINT field cannot be negative", ParseError.INVALID_FIELD_VALUE
                    )

                return struct.pack("!I", self.value)

            elif self.field_type == FieldType.DATA:
                if not isinstance(self.value, bytes):
                    raise ParseError(
                        "Data field must have bytes value", ParseError.INVALID_FIELD_VALUE
                    )
                return struct.pack(f"!H{len(self.value)}s", len(self.value), self.value)

            else:
                raise ParseError(
                    f"Unsupported field type: {self.field_type}", ParseError.INVALID_FIELD_TYPE
                )

        except Exception as e:
            raise ParseError(
                f"Failed to convert field value to bytes: {str(e)}", ParseError.INVALID_FIELD_VALUE
            ) from e

    @classmethod
    def from_bytes(cls, field_type: FieldType, data: bytes) -> "Field":
        """Convert bytes to a Field object according to N210 spec section 3.2"""
        try:
            if field_type == FieldType.STRING:
                length = struct.unpack("!H", data[:2])[0]
                value = data[2 : 2 + length].decode("utf-8")
                return cls(field_type, value)

            elif field_type == FieldType.BOOLEAN:
                value = struct.unpack("!B", data[:1])[0] == 1
                return cls(field_type, value)

            elif field_type in (FieldType.UINT, FieldType.INT, FieldType.ENUM):
                value = struct.unpack("!I", data[: FieldSize.UINT])[0]
                if field_type == FieldType.INT:
                    value = struct.unpack("!i", data[: FieldSize.INT])[0]  # Signed integer
                return cls(field_type, value)

            elif field_type == FieldType.DATA:
                length = struct.unpack("!H", data[:2])[0]
                value = data[2 : 2 + length]
                return cls(field_type, value)

            else:
                raise ParseError(
                    f"Unsupported field type: {field_type}", ParseError.INVALID_FIELD_TYPE
                )

        except Exception as e:
            raise ParseError(
                f"Failed to parse field from bytes: {str(e)}", ParseError.INVALID_FIELD_VALUE
            ) from e
