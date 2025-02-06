"""Tests for MTBP binary protocol implementation.

This module contains tests that verify the binary protocol implementation
conforms to N210 section 1.2.2 requirements for satellite binary encoding.
"""

import pytest

from protocols.mtbp.encoding.binary_parser import BinaryParser
from protocols.mtbp.constants.message_types import MessageType
from protocols.mtbp.validation.exceptions import ParseError


class TestBinaryProtocol:
    """Test suite for MTBP binary protocol implementation."""

    parser: BinaryParser

    def setup_method(self) -> None:
        """Set up test environment before each test."""
        self.parser = BinaryParser()

    def test_uint_parsing(self) -> None:
        """Test parsing of unsigned integers."""
        # Test uint8
        data = bytes([123])
        assert self.parser.parse_uint8(data, 0) == 123

        # Test uint16
        data = bytes([0x12, 0x34])
        assert self.parser.parse_uint16(data, 0) == 0x1234

        # Test uint32
        data = bytes([0x12, 0x34, 0x56, 0x78])
        assert self.parser.parse_uint32(data, 0) == 0x12345678

    def test_int_parsing(self) -> None:
        """Test parsing of signed integers."""
        # Test int8
        data = bytes([0xFF])  # -1 in two's complement
        assert self.parser.parse_int8(data, 0) == -1

        # Test positive int8
        data = bytes([0x7F])  # 127
        assert self.parser.parse_int8(data, 0) == 127

    def test_string_parsing(self) -> None:
        """Test string parsing."""
        data = b"Hello World"
        assert self.parser.parse_string(data, 0, 5) == "Hello"

    def test_boolean_parsing(self) -> None:
        """Test boolean parsing."""
        data = bytes([0x01, 0x00])
        assert self.parser.parse_boolean(data, 0) is True
        assert self.parser.parse_boolean(data, 1) is False

    def test_insufficient_data(self) -> None:
        """Test handling of insufficient data."""
        data = bytes([0x12])

        # Try to parse uint16 from single byte
        with pytest.raises(ParseError) as exc_info:
            self.parser.parse_uint16(data, 0)
        assert exc_info.value.error_code == ParseError.INVALID_SIZE

        # Try to parse uint32 from single byte
        with pytest.raises(ParseError) as exc_info:
            self.parser.parse_uint32(data, 0)
        assert exc_info.value.error_code == ParseError.INVALID_SIZE

    def test_invalid_position(self) -> None:
        """Test parsing from invalid position."""
        data = bytes([0x12, 0x34])

        # Try to parse from position beyond data length
        with pytest.raises(ParseError) as exc_info:
            self.parser.parse_uint8(data, 2)
        assert exc_info.value.error_code == ParseError.INVALID_SIZE

    def test_enum_parsing(self) -> None:
        """Test enum value parsing."""
        data = bytes([0x01])  # MessageType.DATA
        value = self.parser.parse_enum(data, 0)
        assert value == MessageType.DATA.value

    def test_data_parsing(self) -> None:
        """Test binary data parsing."""
        original = bytes([0x01, 0x02, 0x03, 0x04])
        parsed = self.parser.parse_data(original, 0, len(original))
        assert parsed == original

    def test_string_encoding(self) -> None:
        """Test string encoding validation."""
        # Test valid UTF-8 string
        data = "Hello".encode("utf-8")
        result = self.parser.parse_string(data, 0, len(data))
        assert result == "Hello"

        # Test invalid UTF-8 sequence
        data = bytes([0xFF, 0xFF])  # Invalid UTF-8
        with pytest.raises(ParseError) as exc_info:
            self.parser.parse_string(data, 0, len(data))
        assert exc_info.value.error_code == ParseError.DECODE_FAILED
