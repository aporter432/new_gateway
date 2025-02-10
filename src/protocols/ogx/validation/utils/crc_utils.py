"""
Utility functions for CRC calculations.

This module provides CRC calculation functions that may be used in future implementations
to optimize message validation and reduce API overhead. Currently not in active use as
message validation is handled by the OGWS gateway API.

Future Implementation Notes:
    - May be used for local message validation before API submission
    - Could reduce gateway roundtrips for invalid messages
    - Would provide client-side validation for bandwidth optimization
    - Implementation follows CRC-16-CCITT (XMODEM) standard for compatibility
"""

import binascii


def compute_crc16_ccitt(data: bytes) -> int:
    """
    Computes CRC-16-CCITT (XMODEM) checksum for potential future local validation.

    Implementation details:
    - Polynomial: x^16 + x^15 + x^2 + 1 (0x1021)
    - Initial value: 0xFFFF
    - No final XOR
    - Input not reversed
    - Output not reversed

    This implementation uses Python's binascii.crc_hqx which implements the exact
    same algorithm for future compatibility.

    Args:
        data (bytes): The binary data to compute CRC for.

    Returns:
        int: Computed CRC-16 value as an unsigned 16-bit integer.
    """
    return binascii.crc_hqx(data, 0xFFFF)
