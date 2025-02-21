"""Tests for service limits and size calculation functions."""

import pytest

from Protexis_Command.protocol.ogx.constants.ogx_limits import (
    MAX_OGX_PAYLOAD_BYTES,
    calculate_base64_size,
    calculate_json_overhead,
    validate_payload_size,
)


class TestSizeCalculations:
    """Test size calculation helper functions."""

    @pytest.mark.parametrize(
        "binary_size,expected",
        [
            (0, 0),  # Empty input
            (1, 4),  # Single byte -> 4 chars with padding
            (2, 4),  # Two bytes -> 4 chars with padding
            (3, 4),  # Three bytes -> 4 chars exact
            (4, 8),  # Four bytes -> 8 chars with padding
            (100, 136),  # Larger input
        ],
    )
    def test_calculate_base64_size(self, binary_size, expected):
        """Test base64 size calculation with various inputs."""
        assert calculate_base64_size(binary_size) == expected

    @pytest.mark.parametrize(
        "base64_size,expected",
        [
            (0, 50),  # Empty base64 string
            (4, 54),  # Small base64 string
            (100, 150),  # Larger base64 string
        ],
    )
    def test_calculate_json_overhead(self, base64_size, expected):
        """Test JSON overhead calculation."""
        assert calculate_json_overhead(base64_size) == expected

    @pytest.mark.parametrize(
        "binary_size,expected",
        [
            (0, True),  # Empty payload
            (1023, True),  # Maximum allowed size
            (1024, False),  # Exceeds limit
            (2000, False),  # Well over limit
        ],
    )
    def test_validate_payload_size(self, binary_size, expected):
        """Test payload size validation."""
        assert validate_payload_size(binary_size) == expected

    def test_size_calculation_workflow(self):
        """Test complete size calculation workflow."""
        # Test a typical use case
        binary_size = 100
        base64_size = calculate_base64_size(binary_size)
        json_size = calculate_json_overhead(base64_size)

        assert base64_size == 136  # 100 bytes -> 136 base64 chars
        assert json_size == 186  # 136 + 50 overhead
        assert validate_payload_size(binary_size)  # Within 1023 limit

        # Test a borderline case
        binary_size = MAX_OGX_PAYLOAD_BYTES
        assert validate_payload_size(binary_size)  # Should be exactly at limit
        base64_size = calculate_base64_size(binary_size)
        json_size = calculate_json_overhead(base64_size)
        assert json_size > base64_size  # Verify overhead is added
