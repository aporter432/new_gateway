"""Message types as defined in OGWS-1.txt.

This module defines the message direction types for OGWS communication:
- To-mobile (forward/FW): Messages sent to terminals from gateway
- From-mobile (return/RE): Messages sent from terminals to gateway

Message Type Characteristics (from OGWS-1.txt):
- To-mobile (FW):
    - Requires valid destination terminal or broadcast ID
    - Subject to outstanding message limits (10 per size class)
    - Can specify transport type (Satellite/Cellular/Any)
    - Can include UserMessageID for client tracking
    - Supports delayed send options (IDP only)
    - Message states: ACCEPTED, RECEIVED, ERROR, etc.

- From-mobile (RE):
    - Includes source terminal's prime ID
    - Retrieved using high-watermark tracking
    - Maximum 500 messages per response
    - Retention period: 5 days
    - Includes message timestamp (MessageUTC)
    - Can include raw or decoded payload

OGWS API Interaction Examples:

    # All API calls require bearer token authentication
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    # Example 1: Submit to-mobile message
    # POST https://ogws.orbcomm.com/api/v1.0/submit/messages
    submit_request = {
        "DestinationID": "01008988SKY5909",
        "UserMessageID": 2097,
        "Payload": {
            "Name": "getTerminalStatus",
            "SIN": 16,
            "MIN": 2,
            "IsForward": True,
            "Fields": []
        }
    }
    # Response includes message state
    submit_response = {
        "ErrorID": 0,
        "Submissions": [{
            "ID": 10844864715,
            "DestinationID": "01008988SKY5909",
            "UserMessageID": 2097,
            "State": MessageType.FW_ACCEPTED
        }]
    }

    # Example 2: Retrieve from-mobile messages
    # GET https://ogws.orbcomm.com/api/v1.0/get/re_messages?FromUTC=2022-11-25+12:00:00
    get_messages_params = {
        "FromUTC": "2022-11-25 12:00:00",
        "IncludeTypes": True,
        "IncludeRawPayload": False
    }
    # Response includes messages and next high-watermark
    get_messages_response = {
        "ErrorID": 0,
        "NextFromUTC": "2022-11-25 12:00:23",
        "Messages": [{
            "ID": 10979489832,
            "MessageUTC": "2022-11-25 12:00:03",
            "MobileID": "01008988SKY5909",
            "SIN": 128
        }]
    }

    # Example 3: Get message status
    # GET https://ogws.orbcomm.com/api/v1.0/get/fw_statuses?IDList=10844864715
    status_response = {
        "ErrorID": 0,
        "Statuses": [{
            "ID": 10844864715,
            "State": MessageType.FW_RECEIVED,
            "IsClosed": True,
            "CreateUTC": "2022-11-25 12:00:20",
            "StatusUTC": "2022-11-25 12:00:23"
        }]
    }

Implementation Notes from OGWS-1.txt:
    - All API calls require bearer token authentication
    - API base URL: https://ogws.orbcomm.com/api/v1.0
    - To-mobile messages require destination validation
    - From-mobile messages use high-watermark tracking
    - Message retention limited to 5 days
    - Maximum 500 messages per retrieval
    - Message IDs are Gateway-generated
    - UserMessageID optional for client tracking
    - Status updates track message lifecycle
    - Consider message timeout periods
"""

from enum import IntEnum


class MessageType(IntEnum):
    """Message types and states as defined in OGWS-1.txt.

    Attributes:
        FW_ACCEPTED (0): To-mobile message accepted by OGWS
        FW_RECEIVED (1): To-mobile message acknowledged by destination
        FW_ERROR (2): Submission error (check error code)
        FW_DELIVERY_FAILED (3): Message failed to deliver
        FW_TIMED_OUT (4): Message timed out
        FW_CANCELLED (5): Message cancelled
        FW_WAITING (6): Message queued for delayed send (IDP only)
        FW_BROADCAST_SUBMITTED (7): Broadcast message transmitted
        FW_SENDING (8): Message sending in progress (OGx only)

    API Usage:
        # Message status in fw_statuses response
        {
            "ErrorID": 0,
            "Statuses": [{
                "ID": 10844864715,
                "State": MessageType.FW_RECEIVED,
                "IsClosed": True
            }]
        }
    """

    # To-mobile (forward) message states
    FW_ACCEPTED = 0
    FW_RECEIVED = 1
    FW_ERROR = 2
    FW_DELIVERY_FAILED = 3
    FW_TIMED_OUT = 4
    FW_CANCELLED = 5
    FW_WAITING = 6
    FW_BROADCAST_SUBMITTED = 7
    FW_SENDING = 8
