"""Transport types as defined in OGx-1.txt Section 4.3.1.

Transport options for message delivery:
0 - ANY: Any transport (satellite or cellular)
1 - SATELLITE: Satellite transport only
2 - CELLULAR: Cellular transport only
"""

from enum import IntEnum


class TransportType(IntEnum):
    """Transport types from OGx-1.txt Section 4.3.1."""

    ANY = 0  # Default if not specified
    SATELLITE = 1  # Never sent over cellular
    CELLULAR = 2  # Cellular network only
