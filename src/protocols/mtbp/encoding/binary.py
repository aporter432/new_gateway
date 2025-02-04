"""
Binary data parsing utilities for MTBP protocol
"""

from src.protocols.mtbp.validation.exceptions import ParseError


class BinaryParser:
    """Handles binary data parsing operations"""

    @staticmethod
    def parse_uint8(data: bytes, position: int) -> int:
        """Parse 1-byte unsigned integer"""
        if len(data) < position + 1:
            raise ParseError(
                f"Insufficient data for uint8 at position {position}",
                error_code=ParseError.INVALID_SIZE,
            )
        return data[position]

    @staticmethod
    def parse_uint16(data: bytes, position: int) -> int:
        """Parse 2-byte unsigned integer"""
        if len(data) < position + 2:
            raise ParseError(
                f"Insufficient data for uint16 at position {position}",
                error_code=ParseError.INVALID_SIZE,
            )
        return int.from_bytes(data[position : position + 2], byteorder="big", signed=False)

    @staticmethod
    def parse_uint32(data: bytes, position: int) -> int:
        """Parse 4-byte unsigned integer"""
        if len(data) < position + 4:
            raise ParseError(
                f"Insufficient data for uint32 at position {position}",
                error_code=ParseError.INVALID_SIZE,
            )
        return int.from_bytes(data[position : position + 4], byteorder="big", signed=False)

    @staticmethod
    def parse_int8(data: bytes, position: int) -> int:
        """Parse 1-byte signed integer"""
        if len(data) < position + 1:
            raise ParseError(
                f"Insufficient data for int8 at position {position}",
                error_code=ParseError.INVALID_SIZE,
            )
        return int.from_bytes(data[position : position + 1], byteorder="big", signed=True)

    @staticmethod
    def parse_int16(data: bytes, position: int) -> int:
        """Parse 2-byte signed integer"""
        if len(data) < position + 2:
            raise ParseError(
                f"Insufficient data for int16 at position {position}",
                error_code=ParseError.INVALID_SIZE,
            )
        return int.from_bytes(data[position : position + 2], byteorder="big", signed=True)

    @staticmethod
    def parse_int32(data: bytes, position: int) -> int:
        """Parse 4-byte signed integer"""
        if len(data) < position + 4:
            raise ParseError(
                f"Insufficient data for int32 at position {position}",
                error_code=ParseError.INVALID_SIZE,
            )
        return int.from_bytes(data[position : position + 4], byteorder="big", signed=True)

    @staticmethod
    def parse_string(data: bytes, position: int, length: int) -> str:
        """Parse UTF-8 string"""
        if length < 0:
            raise ParseError(
                f"Invalid string length {length} at position {position}",
                error_code=ParseError.INVALID_FIELD_VALUE,
            )
        if len(data) < position + length:
            raise ParseError(
                f"Insufficient data for string at position {position}",
                error_code=ParseError.INVALID_SIZE,
            )
        try:
            return data[position : position + length].decode("utf-8").rstrip("\x00")
        except UnicodeDecodeError as e:
            raise ParseError(
                f"Invalid UTF-8 string at position {position}", error_code=ParseError.DECODE_FAILED
            ) from e

    @staticmethod
    def parse_boolean(data: bytes, position: int) -> bool:
        """Parse boolean value"""
        if len(data) < position + 1:
            raise ParseError(
                f"Insufficient data for boolean at position {position}",
                error_code=ParseError.INVALID_SIZE,
            )
        value = data[position]
        return bool(value)

    @staticmethod
    def parse_enum(data: bytes, position: int) -> int:
        """Parse enumerated value"""
        return BinaryParser.parse_uint8(data, position)

    @staticmethod
    def parse_data(data: bytes, position: int, length: int) -> bytes:
        """Parse raw data field"""
        if length < 0:
            raise ParseError(
                f"Invalid data length {length} at position {position}",
                error_code=ParseError.INVALID_FIELD_VALUE,
            )
        if len(data) < position + length:
            raise ParseError(
                f"Insufficient data for raw data at position {position}",
                error_code=ParseError.INVALID_SIZE,
            )
        return data[position : position + length]
