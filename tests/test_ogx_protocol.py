"""Tests for OGx protocol message size validation according to OGWS-1.txt."""

from src.protocols.ogx.encoding.binary.encoder import BinaryEncoder
from src.protocols.ogx.constants.limits import MAX_OGX_PAYLOAD_BYTES
from src.protocols.ogx.validation.common.validation_exceptions import SizeValidationError


class TestSizeValidation:
    """Test suite for raw payload size validation.

    Key concepts:
    1. The 1023 byte limit applies to raw binary data BEFORE Base64 encoding
    2. Base64 encoding overhead (~33%) does not count against this limit
    3. CRC and message framing are handled by OGWS internally
    """

    def test_size_limit(self):
        """Test raw payload size validation."""
        # Calculate overhead for empty message structure
        template = {"payload": ""}
        overhead = len(BinaryEncoder._encode_dict(template))

        # Test exactly at size limit
        data = {"payload": "x" * (MAX_OGX_PAYLOAD_BYTES - overhead)}
        binary = BinaryEncoder._encode_dict(data)
        assert len(binary) <= MAX_OGX_PAYLOAD_BYTES

        # Test one byte over limit
        data = {"payload": "x" * (MAX_OGX_PAYLOAD_BYTES - overhead + 1)}
        try:
            BinaryEncoder._encode_dict(data)
            assert False, "Should have raised ValueError for exceeding raw payload limit"
        except ValueError:
            pass  # Expected

    def test_empty_payload(self):
        """Test validation of empty payload."""
        data = {"payload": ""}
        binary = BinaryEncoder._encode_dict(data)
        assert len(binary) < MAX_OGX_PAYLOAD_BYTES

    def test_complex_payload(self):
        """Test validation with complex nested structure."""
        data = {
            "header": {
                "id": 123,
                "timestamp": "2023-01-01T00:00:00Z",
            },
            "payload": "x" * 100,  # Some reasonable payload size
            "metadata": {"type": "test", "version": "1.0"},
        }
        binary = BinaryEncoder._encode_dict(data)
        assert len(binary) < MAX_OGX_PAYLOAD_BYTES
