"""
MTBP header parser.
"""

from src.protocols.mtbp.validation.exceptions import ParseError
from src.protocols.mtbp.encoding.binary_parser import BinaryParser
from src.protocols.utils.crc_utils import compute_crc16_ccitt


class HeaderParser:
    """Handles MTBP message header parsing"""

    HEADER_SIZE = 6  # SIN(1) + MIN(1) + Length(2) + CRC(2)
    CRC_SIZE = 2

    @staticmethod
    def parse_header(data: bytes) -> dict:
        """
        Parses the message header, extracting SIN, MIN, message length, and CRC.

        Args:
            data (bytes): The raw binary message.

        Returns:
            dict: Parsed header fields including SIN, MIN, length, and CRC.

        Raises:
            ParseError: If header is malformed, too short, or has CRC issues.
        """
        if len(data) < HeaderParser.HEADER_SIZE + HeaderParser.CRC_SIZE:
            raise ParseError(
                "Insufficient data for header parsing", error_code=ParseError.INVALID_SIZE
            )

        # Extract header fields using BinaryParser
        sin = BinaryParser.parse_uint8(data, 0)
        min_id = BinaryParser.parse_uint8(data, 1)
        message_length = BinaryParser.parse_uint16(data, 2)
        crc_received = BinaryParser.parse_uint16(data, 4)

        # Expected total length check (including CRC)
        expected_length = message_length + HeaderParser.HEADER_SIZE + HeaderParser.CRC_SIZE
        if len(data) < expected_length:
            raise ParseError(
                f"Message length mismatch: expected {expected_length}, got {len(data)}",
                error_code=ParseError.INVALID_SIZE,
            )

        # Compute CRC from actual data excluding received CRC
        computed_crc = compute_crc16_ccitt(data[: -HeaderParser.CRC_SIZE])
        if crc_received != computed_crc:
            raise ParseError(
                f"CRC mismatch: received {crc_received:#06x}, expected {computed_crc:#06x}",
                error_code=ParseError.INVALID_CHECKSUM,
            )

        return {"SIN": sin, "MIN": min_id, "Length": message_length, "CRC": crc_received}
