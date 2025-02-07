"""Network types for OGWS terminals.

This module defines the available network types for OGWS terminals as specified in OGWS-1.txt.
Each network type has specific characteristics affecting message handling, payload limits,
and operational capabilities.

Network Characteristics (from OGWS-1.txt):
- IsatData Pro (0):
    - Payload limits: 
        - Small messages: up to 400 bytes
        - Medium messages: up to 2000 bytes
        - Large messages: up to 10,000 bytes
    - Maximum 10 outstanding messages per size class
    - Message timeout: 120 minutes
    - Supports broadcast messaging
    - Supports ALWAYS_ON and WAKE_UP operation modes
    
- OGx (1):
    - Fixed payload limit: up to 1,023 bytes
    - Message timeout: 10 days
    - Supports all operation modes
    - Cellular/Satellite hybrid capabilities

API Usage Examples:

    from protocols.ogx.constants import NetworkType
    
    # Example 1: Checking network in message status response
    status_response = {
        "ID": 10844864715,
        "Network": NetworkType.ISAT_DATA_PRO,
        "State": 1,
        "Transport": 1
    }
    
    # Network-specific timeout handling
    if status_response["Network"] == NetworkType.ISAT_DATA_PRO:
        timeout_minutes = 120  # IDP timeout
    else:
        timeout_minutes = 14400  # OGx 10-day timeout
    
    # Example 2: Network-specific payload validation
    def validate_payload(network: NetworkType, payload_size: int) -> bool:
        '''Validate payload size per OGWS spec.'''
        if network == NetworkType.ISAT_DATA_PRO:
            # IDP has size classes with different limits
            return payload_size <= 10000  # Max IDP size
        # OGx has fixed limit
        return payload_size <= 1023
    
    # Example 3: Network in terminal info response
    terminal_info = {
        "PrimeID": "01000005SKYCD96",
        "LastSatelliteNetwork": NetworkType.OGX,
        "LastOperationMode": 0
    }

Implementation Notes from OGWS-1.txt:
    - Network type determines message timeout period
    - Message size limits strictly enforced per network
    - Outstanding message limits vary by network
    - Network affects available transport options
    - Consider network capabilities for message delivery
    - Network determines available operation modes
    - Check network support for broadcast messages
    - Network affects message state transitions
"""

from enum import IntEnum


class NetworkType(IntEnum):
    """Network types as defined in OGWS-1.txt.

    Attributes:
        ISAT_DATA_PRO (0): IsatData Pro network
            - Variable message sizes (400B, 2000B, 10000B)
            - 120 minute message timeout
            - Broadcast messaging support
            - Limited to ALWAYS_ON and WAKE_UP modes

        OGX (1): OGx network
            - Fixed 1023B payload limit
            - 10 day message timeout
            - All operation modes supported
            - Cellular/Satellite hybrid capable

    API Response Examples:
        # Terminal registration response
        {
            "LastSatelliteNetwork": NetworkType.OGX,
            "LastOperationMode": 0,
            "LastRegionName": "AMERRB9"
        }

        # Message status response
        {
            "Network": NetworkType.ISAT_DATA_PRO,
            "Transport": 1,
            "State": 1
        }
    """

    ISAT_DATA_PRO = 0  # IsatData Pro network
    OGX = 1  # OGx network
