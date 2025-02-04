"""
Handles field serialization for MTBP messages according to N210 spec section 3.2.
"""

import struct

from src.protocols.mtbp.constants.field_types import FieldType
from src.protocols.mtbp.validation.exceptions import ParseError


class FieldSerializer:
    """
    Serializes and deserializes MTBP fields as per N210 specification.
    """

    @staticmethod
    def to_bytes(field) -> bytes:
        """Convert field value to bytes according to N210 spec section 3.2."""
        try:
            if field.field_type == FieldType.STRING:
                if not isinstance(field.value, str):
                    raise ParseError(
                        "String field must have str value", ParseError.INVALID_FIELD_VALUE
                    )
                encoded_value = field.value.encode("utf-8")
                return struct.pack(f"!H{len(encoded_value)}s", len(encoded_value), encoded_value)

            elif field.field_type == FieldType.BOOLEAN:
                if not isinstance(field.value, bool):
                    raise ParseError(
                        "Boolean field must have bool value", ParseError.INVALID_FIELD_VALUE
                    )
                return struct.pack("!B", 1 if field.value else 0)

            elif field.field_type in (FieldType.UINT, FieldType.INT, FieldType.ENUM):
                if not isinstance(field.value, int):
                    raise ParseError(
                        f"{field.field_type.name} field must have int value",
                        ParseError.INVALID_FIELD_VALUE,
                    )
                if field.field_type == FieldType.UINT and field.value < 0:
                    raise ParseError(
                        "UINT field cannot be negative", ParseError.INVALID_FIELD_VALUE
                    )

                byte_size = (field.value.bit_length() + 7) // 8 or 1
                return struct.pack(f"!{byte_size}B", *field.value.to_bytes(byte_size, "big"))

            elif field.field_type == FieldType.DATA:
                if not isinstance(field.value, bytes):
                    raise ParseError(
                        "Data field must have bytes value", ParseError.INVALID_FIELD_VALUE
                    )
                return struct.pack(f"!H{len(field.value)}s", len(field.value), field.value)

            else:
                raise ParseError(
                    f"Unsupported field type: {field.field_type}", ParseError.INVALID_FIELD_TYPE
                )

        except Exception as e:
            raise ParseError(
                f"Failed to convert field value to bytes: {str(e)}", ParseError.INVALID_FIELD_VALUE
            ) from e

    @staticmethod
    def from_bytes(field_type: FieldType, data: bytes):
        """Convert bytes back into a field value according to N210 spec section 3.2."""
        try:
            if field_type == FieldType.STRING:
                length = struct.unpack("!H", data[:2])[0]
                return data[2 : 2 + length].decode("utf-8")

            elif field_type == FieldType.BOOLEAN:
                return bool(struct.unpack("!B", data[:1])[0])

            elif field_type in (FieldType.UINT, FieldType.INT, FieldType.ENUM):
                int_value = int.from_bytes(data, "big")
                if field_type == FieldType.UINT and int_value < 0:
                    raise ParseError(
                        "UINT field cannot be negative", ParseError.INVALID_FIELD_VALUE
                    )
                return int_value

            elif field_type == FieldType.DATA:
                length = struct.unpack("!H", data[:2])[0]
                return data[2 : 2 + length]

            else:
                raise ParseError(
                    f"Unsupported field type: {field_type}", ParseError.INVALID_FIELD_TYPE
                )

        except Exception as e:
            raise ParseError(
                f"Failed to parse bytes to field value: {str(e)}", ParseError.INVALID_FIELD_VALUE
            ) from e
