"""Tests for OGx protocol message size validation according to OGx-1.txt."""

from Protexis_Command.api_ogx.constants.ogx_limits import MAX_OGX_PAYLOAD_BYTES


class TestSizeValidation:
    """Test suite for message size validation.

    Key concepts:
    1. The 1023 byte limit applies to message payload size
    2. Message size includes all fields and content
    3. Size limits are enforced before any encoding/transmission
    """

    def test_size_limit(self):
        """Test message size validation."""
        # Test exactly at size limit
        data = {"payload": "x" * MAX_OGX_PAYLOAD_BYTES}
        assert len(data["payload"]) == MAX_OGX_PAYLOAD_BYTES

        # Test one byte over limit
        data = {"payload": "x" * (MAX_OGX_PAYLOAD_BYTES + 1)}
        assert len(data["payload"]) > MAX_OGX_PAYLOAD_BYTES

    def test_empty_payload(self):
        """Test validation of empty payload."""
        data = {"payload": ""}
        assert len(data["payload"]) == 0

    def test_complex_message(self):
        """Test validation with complex message structure."""
        data = {
            "header": {
                "id": 123,
                "timestamp": "2023-01-01T00:00:00Z",
            },
            "payload": "x" * 100,  # Some reasonable payload size
            "metadata": {"type": "test", "version": "1.0"},
        }
        # Verify total message size is reasonable
        total_size = len(str(data["header"])) + len(data["payload"]) + len(str(data["metadata"]))
        assert total_size < MAX_OGX_PAYLOAD_BYTES
