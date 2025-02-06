"""
Binary data parsing utilities for MTBP protocol

Handles decoding of binary messages, including headers, fields, and CRC validation.
"""

from src.protocols.mtbp.validation.exceptions import ParseError
from src.protocols.utils.crc_utils import compute_crc16_ccitt


class BinaryParser:
    """Handles binary data parsing operations for MTBP protocol."""

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
    def parse_header(data: bytes) -> dict:
        """Parse message header including SIN, MIN, and length."""
        if len(data) < 6:
            raise ParseError(
                "Insufficient data for message header", error_code=ParseError.INVALID_SIZE
            )
        header = {
            "SIN": BinaryParser.parse_uint8(data, 0),
            "MIN": BinaryParser.parse_uint8(data, 1),
            "length": BinaryParser.parse_uint16(data, 2),
            "CRC": BinaryParser.parse_uint16(data, 4),
        }
        return header

    @staticmethod
    def parse_payload(data: bytes, position: int, length: int) -> bytes:
        """Parse raw payload data."""
        if len(data) < position + length:
            raise ParseError("Insufficient data for payload", error_code=ParseError.INVALID_SIZE)
        return data[position : position + length]

    @staticmethod
    def validate_crc(data: bytes) -> bool:
        """Validate CRC checksum from the binary message."""
        if len(data) < 6:
            raise ParseError(
                "Insufficient data for CRC validation", error_code=ParseError.INVALID_SIZE
            )
        received_crc = BinaryParser.parse_uint16(data, 4)
        computed_crc = compute_crc16_ccitt(data[:-2])
        return received_crc == computed_crc

    @staticmethod
    def parse_message(data: bytes) -> dict:
        """Parse full MTBP message including header and payload."""
        header = BinaryParser.parse_header(data)
        payload = BinaryParser.parse_payload(data, 6, header["length"] - 6)
        return {"header": header, "payload": payload}
