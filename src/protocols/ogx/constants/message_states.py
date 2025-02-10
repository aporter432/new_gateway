"""Message states as defined in OGWS-1.txt Section 4.3 Tables 1 & 2."""

from enum import IntEnum


class MessageState(IntEnum):
    """Message states from OGWS-1.txt Section 4.3 Tables 1 & 2."""

    ACCEPTED = 0  # Message accepted by OGWS/IGWS
    RECEIVED = 1  # Message acknowledged by destination
    ERROR = 2  # Submission error (check error code)
    DELIVERY_FAILED = 3  # Message failed to be delivered
    TIMED_OUT = 4  # Message timed out by Gateway/NPC
    CANCELLED = 5  # Message cancelled
    WAITING = 6  # Queued for delayed send (IDP only)
    BROADCAST_SUBMITTED = 7  # Broadcast message transmitted
    SENDING = 8  # Sending in progress (OGx only)
