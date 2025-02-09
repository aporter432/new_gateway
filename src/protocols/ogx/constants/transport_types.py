"""Transport types as defined in OGWS-1.txt

Transport types specify the delivery method for messages:
- ANY (0): Use any available transport (default)
- SATELLITE (1): Use satellite network only
- CELLULAR (2): Use cellular network only

See OGWS-1.txt Section 4.3.1 for details.
"""

from enum import IntEnum


class TransportType(IntEnum):
    """Transport types as defined in OGWS-1.txt Section 4.3.1"""

    ANY = 0  # Default - use any available transport
    SATELLITE = 1  # Satellite network only
    CELLULAR = 2  # Cellular network only


# Constants for comparison
TRANSPORT_TYPE_ANY = TransportType.ANY
TRANSPORT_TYPE_SATELLITE = TransportType.SATELLITE
TRANSPORT_TYPE_CELLULAR = TransportType.CELLULAR
