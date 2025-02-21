"""Network types for OGx terminals.

This module defines the available network types for OGx terminals as specified in OGx-1.txt.
Each network type has specific characteristics affecting message handling, payload limits,
and operational capabilities.

Network Characteristics (from OGx-1.txt):
- OGx:
    - Fixed payload limit: up to 1,023 bytes
    - Message timeout: 10 days
    - Supports all operation modes
    - Cellular/Satellite hybrid capabilities

API Usage Examples:

    from Protexis_Command.api_ogx.constants import NetworkType

    # Example 1: Checking network in message status response
    status_response = {
        "ID": 10844864715,
        "Network": NetworkType.OGX,
        "State": 1,
        "Transport": 1
    }

    # Example 2: Network-specific payload validation
    def validate_payload(payload_size: int) -> bool:
        '''Validate payload size per OGx spec.'''
        return payload_size <= 1023  # OGx fixed limit

Implementation Notes from OGx-1.txt:
    - Message timeout period: 10 days
    - Fixed message size limit: 1,023 bytes
    - Network affects available transport options
    - Consider network capabilities for message delivery
    - Network determines available operation modes
    - Network affects message state transitions
"""

from enum import Enum


class NetworkType(Enum):
    """Network types as defined in OGx-1.txt

    Values:
        ISATDATA_PRO (0): IsatData Pro network
        OGX (1): OGx network
    """

    ISATDATA_PRO = 0  # IsatData Pro network
    OGX = 1  # OGx network

    def __str__(self) -> str:
        """Return string representation of the network type value."""
        return str(self.value)


# Constants for comparison
NETWORK_TYPE_OGX = NetworkType.OGX
