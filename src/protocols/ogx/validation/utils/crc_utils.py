"""
Utility functions for CRC calculations.

This module provides CRC calculation functions that comply with the Orbcomm protocol
specifications for error detection.
"""

import binascii


def compute_crc16_ccitt(data: bytes) -> int:
    """
    Computes CRC-16-CCITT (XMODEM) checksum as specified in the Orbcomm protocol.

    Implementation details:
    - Polynomial: x^16 + x^15 + x^2 + 1 (0x1021)
    - Initial value: 0xFFFF
    - No final XOR
    - Input not reversed
    - Output not reversed

    This implementation uses Python's binascii.crc_hqx which implements the exact
    same algorithm as required by the protocol.

    Args:
        data (bytes): The binary data to compute CRC for.

    Returns:
        int: Computed CRC-16 value as an unsigned 16-bit integer.
    """
    return binascii.crc_hqx(data, 0xFFFF)
