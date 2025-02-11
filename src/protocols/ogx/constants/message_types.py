"""Message directions as defined in OGWS-1.txt Section 4.3.

There are two fundamental message directions:
- To-mobile (forward/FW): Messages sent to terminals from gateway
- From-mobile (return/RE): Messages sent from terminals to gateway
"""

from enum import Enum


class MessageType(str, Enum):
    """Message direction types from OGWS-1.txt Section 4.3."""

    FORWARD = "FW"  # To-mobile message
    RETURN = "RE"  # From-mobile message
