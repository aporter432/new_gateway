"""
MTBP Field Parser
"""

from typing import Any, Union, Tuple
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
    def parse_field(data: bytes, position: int, field_type: str) -> Tuple[Any, int]:
        """
        Parses a single field from binary data based on its type.

        Args:
            data (bytes): The raw binary message.
            position (int): Position in the binary data where the field starts.
            field_type (str): The expected field type (e.g., "UINT8", "UINT16", "STRING").

        Returns:
            Tuple[Any, int]: Tuple containing (parsed value, number of bytes consumed)

        Raises:
            ParseError: If data is insufficient or invalid for the field type.
        """
        try:
            field_type = field_type.upper()

            # Handle fixed-size numeric types
            if field_type == "UINT8":
                return BinaryParser.parse_uint8(data, position), 1
            elif field_type == "UINT16":
                return BinaryParser.parse_uint16(data, position), 2
            elif field_type == "UINT32":
                return BinaryParser.parse_uint32(data, position), 4
            elif field_type == "INT8":
                val = BinaryParser.parse_uint8(data, position)
                return (val - (1 << 8) if val & (1 << 7) else val), 1
            elif field_type == "INT16":
                val = BinaryParser.parse_uint16(data, position)
                return (val - (1 << 16) if val & (1 << 15) else val), 2
            elif field_type == "INT32":
                val = BinaryParser.parse_uint32(data, position)
                return (val - (1 << 32) if val & (1 << 31) else val), 4
            elif field_type == "BOOLEAN":
                return bool(BinaryParser.parse_uint8(data, position)), 1
            elif field_type == "STRING":
                # String format: length (1 byte) followed by UTF-8 encoded string
                if len(data) < position + 1:
                    raise ParseError(
                        "Insufficient data for string length",
                        error_code=ParseError.INVALID_SIZE,
                    )
                length = BinaryParser.parse_uint8(data, position)
                if len(data) < position + 1 + length:
                    raise ParseError(
                        "Insufficient data for string content",
                        error_code=ParseError.INVALID_SIZE,
                    )
                try:
                    string_value = data[position + 1 : position + 1 + length].decode("utf-8")
                    return string_value, length + 1
                except UnicodeDecodeError as e:
                    raise ParseError(
                        f"Invalid UTF-8 string data: {str(e)}",
                        error_code=ParseError.INVALID_FIELD_VALUE,
                    ) from e
            elif field_type == "ENUM":
                # Enums are stored as UINT8
                return BinaryParser.parse_uint8(data, position), 1
            elif field_type == "DATA":
                # Binary data format: length (2 bytes) followed by raw data
                if len(data) < position + 2:
                    raise ParseError(
                        "Insufficient data for binary length",
                        error_code=ParseError.INVALID_SIZE,
                    )
                length = BinaryParser.parse_uint16(data, position)
                if len(data) < position + 2 + length:
                    raise ParseError(
                        "Insufficient data for binary content",
                        error_code=ParseError.INVALID_SIZE,
                    )
                data_value = data[position + 2 : position + 2 + length]
                return data_value, length + 2
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
