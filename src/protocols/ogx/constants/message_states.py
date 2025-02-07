"""Message states as defined in OGWS-1.txt.

This module defines:
- Message states for tracking message delivery status

Message State Characteristics (from OGWS-1.txt):
- OGx Network States:
    - ACCEPTED (0): Message accepted by OGWS
    - RECEIVED (1): Message acknowledged by destination
    - ERROR (2): Submission error (check error code)
    - DELIVERY_FAILED (3): Message failed to deliver
    - TIMED_OUT (4): Message timed out (10 days)
    - CANCELLED (5): Message cancelled
    - BROADCAST_SUBMITTED (7): Broadcast message transmitted
    - SENDING_IN_PROGRESS (8): Message sending in progress

- IsatData Pro Network States:
    - ACCEPTED (0): Message queued by Gateway
    - RECEIVED (1): Terminal acknowledged receipt
    - ERROR (2): Error occurred (check error code)
    - DELIVERY_FAILED (3): Delivery failed
    - TIMED_OUT (4): Not delivered within 120 minutes
    - CANCELLED (5): Cancelled by client
    - WAITING (6): Queued for delayed send
    - BROADCAST_SUBMITTED (7): Broadcast submitted



OGWS API Usage Examples:

    # Example 1: Submit message with transport type
    # POST https://ogws.orbcomm.com/api/v1.0/submit/messages
    submit_request = {
        "DestinationID": "01008988SKY5909",
        "UserMessageID": 2097,
        "TransportType": TransportType.SATELLITE,
        "Payload": {
            "Name": "getTerminalStatus",
            "SIN": 16,
            "MIN": 2,
            "IsForward": True,
            "Fields": []
        }
    }

    # Example 2: Check message status response
    # GET https://ogws.orbcomm.com/api/v1.0/get/fw_statuses?IDList=10844864715
    status_response = {
        "ErrorID": 0,
        "Statuses": [{
            "ID": 10844864715,
            "State": MessageState.RECEIVED,  # Message delivered
            "IsClosed": True,
            "Transport": TransportType.SATELLITE
        }]
    }

    # Example 3: Submit with delayed send (IDP only)
    # POST https://ogws.orbcomm.com/api/v1.0/submit/messages
    delayed_request = {
        "DestinationID": "01097623SKY2C68",
        "DelayedSendOptions": {
            "DelayedSend": True,
            "MessageExpireUTC": "2024-01-25 12:00:00"
        },
        "Payload": {...}
    }
    # Check status - should be WAITING
    delayed_status = {
        "ID": 10844864999,
        "State": MessageState.WAITING,
        "IsClosed": False
    }

Implementation Notes from OGWS-1.txt:
    - Message states indicate delivery progress
    - Transport type affects delivery path and timing
    - State transitions are one-way
    - Some states are network-specific
    - Error states include error codes
    - Timeout periods vary by network
    - Status updates available via fw_statuses endpoint
    - Transport selection may affect message priority
"""

from enum import IntEnum


class MessageState(IntEnum):
    """Message states as defined in OGWS-1.txt section 4.3.

    Attributes:
        ACCEPTED (0): Message accepted by OGWS/IGWS
        RECEIVED (1): Message acknowledged by destination
        ERROR (2): Submission error (check error code)
        DELIVERY_FAILED (3): Message failed to deliver
        TIMED_OUT (4): Message timed out
        CANCELLED (5): Message cancelled
        WAITING (6): Queued for delayed send (IDP only)
        BROADCAST_SUBMITTED (7): Broadcast message transmitted
        SENDING_IN_PROGRESS (8): Sending in progress (OGx only)

    API Response Example:
        # Status response from fw_statuses endpoint
        {
            "ErrorID": 0,
            "Statuses": [{
                "ID": 10844864715,
                "State": MessageState.RECEIVED,
                "IsClosed": True,
                "Transport": 1,
                "CreateUTC": "2022-11-25 12:00:20"
            }]
        }
    """

    ACCEPTED = 0
    RECEIVED = 1
    ERROR = 2
    DELIVERY_FAILED = 3
    TIMED_OUT = 4
    CANCELLED = 5
    WAITING = 6  # IDP network only
    BROADCAST_SUBMITTED = 7
    SENDING_IN_PROGRESS = 8  # OGx network only
