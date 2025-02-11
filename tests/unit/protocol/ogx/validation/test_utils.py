import pytest
from protocols.ogx.validation.utils.crc_utils import calculate_crc
from protocols.ogx.validation.utils import __version__


def test_crc_calculation():
    """Test CRC calculation utility."""
    # Test empty data
    assert calculate_crc(b"") == 0

    # Test known data with known CRC
    test_data = b"123456789"  # Standard test data
    assert calculate_crc(test_data) == 0x31C3  # Known CRC-16 result

    # Test large data
    large_data = b"x" * 1000
    crc = calculate_crc(large_data)
    assert isinstance(crc, int)
    assert 0 <= crc <= 0xFFFF


def test_version():
    """Test version is available."""
    assert isinstance(__version__, str)
    assert len(__version__.split(".")) == 3  # Should be semantic version
