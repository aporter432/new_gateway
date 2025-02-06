"""
MTBP header parser.
"""

from src.protocols.mtbp.validation.exceptions import ParseError
from src.protocols.mtbp.encoding.binary_parser import BinaryParser
from src.protocols.utils import compute_crc16_ccitt


class HeaderParser:
    """Handles MTBP message header parsing"""

    HEADER_SIZE = 3  # SIN(1) + MIN(1) + Length(1)
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
        try:
            if len(data) < HeaderParser.HEADER_SIZE + HeaderParser.CRC_SIZE:
                raise IndexError("Data too short for header")

            # Extract header fields using BinaryParser
            sin = BinaryParser.parse_uint8(data, 0)
            min_id = BinaryParser.parse_uint8(data, 1)
            message_length = BinaryParser.parse_uint8(data, 2)  # Length is 1 byte
            crc_received = BinaryParser.parse_uint16(data, 3)  # CRC starts at position 3

            # Expected total length check
            expected_length = message_length + HeaderParser.HEADER_SIZE + HeaderParser.CRC_SIZE
            if len(data) < expected_length:
                raise IndexError(
                    f"Data too short for message: expected {expected_length}, got {len(data)}"
                )

            # Get header and payload for CRC calculation
            header = data[: HeaderParser.HEADER_SIZE]
            payload = data[HeaderParser.HEADER_SIZE + HeaderParser.CRC_SIZE :]
            data_for_crc = header + payload

            # Compute CRC from header + payload
            computed_crc = compute_crc16_ccitt(data_for_crc)
            if crc_received != computed_crc:
                raise ValueError(
                    f"CRC mismatch: received {crc_received:#06x}, expected {computed_crc:#06x}"
                )

            return {"SIN": sin, "MIN": min_id, "length": message_length, "CRC": crc_received}

        except IndexError as e:
            raise ParseError(
                "Insufficient data for header parsing", error_code=ParseError.INVALID_SIZE
            ) from e
        except ValueError as e:
            raise ParseError(str(e), error_code=ParseError.INVALID_CHECKSUM) from e
        except Exception as e:
            raise ParseError(
                f"Failed to parse header: {str(e)}", error_code=ParseError.INVALID_FORMAT
            ) from e
