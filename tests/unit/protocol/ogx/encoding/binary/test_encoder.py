"""Tests for binary encoding according to OGWS-1.txt."""

import base64
import struct
import pytest

from protocols.ogx.encoding.binary.encoder import BinaryEncoder
from protocols.ogx.constants.limits import MAX_OGX_PAYLOAD_BYTES


class TestBinaryEncoder:
    """Test binary encoding for OGx protocol transport."""

    def test_encode_simple_message(self):
        """Test encoding of simple message."""
        data = {"test": "value"}
        binary = BinaryEncoder.encode_message(data)

        # Verify structure:
        # - 2 bytes for dict size (1)
        # - 2 bytes for key length (4)
        # - 4 bytes "test"
        # - 1 byte type marker (string)
        # - 4 bytes value length (5)
        # - 5 bytes "value"
        # - 2 bytes CRC
        assert len(binary) == 2 + 2 + 4 + 1 + 4 + 5 + 2

        # Verify dict size
        assert struct.unpack(">H", binary[0:2])[0] == 1

        # Verify key length and content
        key_len = struct.unpack(">H", binary[2:4])[0]
        assert key_len == 4
        assert binary[4:8] == b"test"

    def test_encode_nested_structure(self):
        """Test encoding of nested structure."""
        data = {"header": {"id": 123, "type": "test"}, "payload": "content"}
        binary = BinaryEncoder.encode_message(data)

        # Verify it contains CRC
        assert len(binary) > 2  # At least some data + CRC

        # Verify we can base64 encode it
        b64 = BinaryEncoder.encode_for_transport(data)
        assert isinstance(b64, str)
        assert base64.b64decode(b64)  # Should be valid base64

    def test_encode_all_types(self):
        """Test encoding of all supported types."""
        data = {
            "string": "test",
            "integer": 42,
            "boolean": True,
            "null": None,
            "array": [1, "two", {"three": 3}],
            "nested": {"key": "value"},
        }
        binary = BinaryEncoder.encode_message(data)

        # Verify we have data + CRC
        assert len(binary) > 2

        # Extract CRC
        crc = struct.unpack(">H", binary[-2:])[0]
        assert isinstance(crc, int)

    def test_consistent_encoding(self):
        """Test that same data produces same binary output."""
        data = {"test": "value"}
        binary1 = BinaryEncoder.encode_message(data)
        binary2 = BinaryEncoder.encode_message(data)
        assert binary1 == binary2

    def test_size_validation(self):
        """Test size validation against raw binary limit."""
        # Calculate overhead for structure
        template = {"payload": ""}
        overhead = len(BinaryEncoder.encode_message(template)) - 2  # Subtract CRC

        # Test at size limit
        data = {"payload": "x" * (MAX_OGX_PAYLOAD_BYTES - overhead)}
        binary = BinaryEncoder.encode_message(data)
        # Raw binary should be within limit
        assert len(binary) - 2 <= MAX_OGX_PAYLOAD_BYTES  # -2 for CRC

        # Test over size limit
        with pytest.raises(ValueError, match=f".*exceeds limit of {MAX_OGX_PAYLOAD_BYTES} bytes"):
            data = {"payload": "x" * (MAX_OGX_PAYLOAD_BYTES - overhead + 1)}
            BinaryEncoder.encode_message(data)

        # Base64 encoding overhead should not affect limit
        data = {"payload": "x" * (MAX_OGX_PAYLOAD_BYTES - overhead - 100)}
        binary = BinaryEncoder.encode_message(data)
        b64 = BinaryEncoder.encode_for_transport(data)
        # Base64 string will be longer but that's ok
        assert len(b64) > len(binary)
