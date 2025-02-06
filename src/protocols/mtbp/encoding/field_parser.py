"""
MTBP Field Parser
"""

from typing import Any, Union
from src.protocols.mtbp.validation.exceptions import ParseError
from src.protocols.mtbp.encoding.binary_parser import BinaryParser


class FieldParser:
    """Handles field-level parsing within an MTBP message."""

    FIELD_SIZES = {
        "UINT8": 1,
        "UINT16": 2,
        "UINT32": 4,
        "UINT64": 8,
        "INT8": 1,
        "INT16": 2,
        "INT32": 4,
        "INT64": 8,
        "BOOLEAN": 1,
    }

    @staticmethod
    def get_field_size(field_type: str) -> Union[int, None]:
        """Get the size in bytes for a given field type."""
        return FieldParser.FIELD_SIZES.get(field_type.upper())

    @staticmethod
    def parse_field(data: bytes, position: int, field_type: str) -> Any:
        """
        Parses a single field from binary data based on its type.

        Args:
            data (bytes): The raw binary message.
            position (int): Position in the binary data where the field starts.
            field_type (str): The expected field type (e.g., "UINT8", "UINT16", "STRING").

        Returns:
            Any: Parsed field value.

        Raises:
            ParseError: If data is insufficient or invalid for the field type.
        """
        try:
            field_type = field_type.upper()

            # Handle fixed-size numeric types
            if field_type == "UINT8":
                return BinaryParser.parse_uint8(data, position)
            elif field_type == "UINT16":
                return BinaryParser.parse_uint16(data, position)
            elif field_type == "UINT32":
                return BinaryParser.parse_uint32(data, position)
            elif field_type == "INT8":
                return (
                    BinaryParser.parse_uint8(data, position) - (1 << 8)
                    if data[position] & (1 << 7)
                    else data[position]
                )
            elif field_type == "INT16":
                val = BinaryParser.parse_uint16(data, position)
                return val - (1 << 16) if val & (1 << 15) else val
            elif field_type == "INT32":
                val = BinaryParser.parse_uint32(data, position)
                return val - (1 << 32) if val & (1 << 31) else val
            elif field_type == "BOOLEAN":
                return bool(BinaryParser.parse_uint8(data, position))
            elif field_type == "STRING":
                # String format: length (1 byte) followed by UTF-8 encoded string
                length = BinaryParser.parse_uint8(data, position)
                if len(data) < position + 1 + length:
                    raise ParseError(
                        "Insufficient data for string field", error_code=ParseError.INVALID_SIZE
                    )
                return data[position + 1 : position + 1 + length].decode("utf-8")
            elif field_type == "ENUM":
                # Enums are stored as UINT8
                return BinaryParser.parse_uint8(data, position)
            elif field_type == "DATA":
                # Binary data format: length (2 bytes) followed by raw data
                length = BinaryParser.parse_uint16(data, position)
                if len(data) < position + 2 + length:
                    raise ParseError(
                        "Insufficient data for binary field", error_code=ParseError.INVALID_SIZE
                    )
                return data[position + 2 : position + 2 + length]
            else:
                raise ParseError(
                    f"Unsupported field type: {field_type}",
                    error_code=ParseError.INVALID_FIELD_TYPE,
                )
        except IndexError as exc:
            raise ParseError(
                f"Field parsing failed due to insufficient data for type {field_type}",
                error_code=ParseError.INVALID_SIZE,
            ) from exc
