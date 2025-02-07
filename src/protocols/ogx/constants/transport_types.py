"""Transport types as defined in OGWS-1.txt.

This module defines the available transport types for OGWS terminals as specified in OGWS-1.txt.
Each transport type has specific characteristics affecting message handling, payload limits,
and operational capabilities.

Transport Types (from OGWS-1.txt):
- ANY (0): Use any available transport
- SATELLITE (1): Use satellite network only
- CELLULAR (2): Use cellular network only
"""

from enum import IntEnum


class TransportType(IntEnum):
    """Transport types as defined in OGWS-1.txt section 4.3.1.

    Attributes:
        ANY (0): Use any available transport (default)
        SATELLITE (1): Use satellite network only
        CELLULAR (2): Use cellular network only

    API Usage Example:
        # Submit message with transport type
        {
            "DestinationID": "01008988SKY5909",
            "TransportType": TransportType.SATELLITE,
            "Payload": {...}
        }
    """

    ANY = 0
    SATELLITE = 1
    CELLULAR = 2
