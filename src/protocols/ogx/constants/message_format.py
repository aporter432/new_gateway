"""Message format constants as defined in OGWS-1.txt.

This module defines the required fields and properties for OGWS messages.

Common Message Format (from OGWS-1.txt):
- Required Fields:
    - Name: Message name (string)
    - SIN: Service identification number (integer 16-255)
    - MIN: Message identification number (integer 1-255)
    - Fields: Array of field objects

- Field Properties:
    - Name: Field identifier
    - Type: Data type (see FieldType enum)
    - Value: Field content
    - Elements: Optional array of indexed elements

- Element Properties:
    - Index: Zero-based position in array
    - Fields: Container for element fields

OGWS API Usage Examples:

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

    # Example 2: From-mobile message response
    # GET https://ogws.orbcomm.com/api/v1.0/get/re_messages
    message_response = {
        "ID": 10844864715,
        "MessageUTC": "2022-11-25 12:00:03",
        "MobileID": "01008988SKY5909",
        "Payload": {
            "Name": "message_name",
            "SIN": 128,
            "MIN": 1,
            "Fields": [{
                "Name": "field_value",
                "Value": "0",
                "Type": "string"
            }]
        }
    }

    # Example 3: Message with array elements
    array_message = {
        "Name": "sensorReadings",
        "SIN": 128,
        "MIN": 2,
        "Fields": [{
            "Name": "readings",
            "Elements": [
                {
                    "Index": 0,
                    "Fields": [
                        {
                            "Name": "temperature",
                            "Value": "25.5",
                            "Type": "float"
                        }
                    ]
                }
            ]
        }]
    }

Implementation Notes from OGWS-1.txt:
    - All required fields must be present and non-null
    - SIN must be between 16-255
    - MIN must be between 1-255
    - Field names are case-sensitive
    - Array elements must have sequential indices
    - RawPayload takes precedence over Payload if both present
    - Field types must match declared types
    - Message validation occurs before encoding
    - Some fields only valid for specific directions
    - Error handling includes detailed context
"""

from enum import Enum
from typing import Final, Set


class MessageDirection(str, Enum):
    """Message direction as defined in OGWS-1.txt.

    Attributes:
        TO_MOBILE: Forward message sent to terminal
        FROM_MOBILE: Return message from terminal

    API Usage Example:
        # Message direction in status response
        {
            "ID": 10844864715,
            "Direction": MessageDirection.TO_MOBILE,
            "State": 1,
            "IsClosed": True
        }
    """

    TO_MOBILE = "to-mobile"  # Forward message
    FROM_MOBILE = "from-mobile"  # Return message


# Required fields for every message per OGWS-1.txt
REQUIRED_MESSAGE_FIELDS: Final[Set[str]] = {
    "Name",  # Message name
    "SIN",  # Service identification number (16-255)
    "MIN",  # Message identification number (1-255)
    "Fields",  # Array of Field instances
}


# Required properties for every field per OGWS-1.txt
REQUIRED_FIELD_PROPERTIES: Final[Set[str]] = {
    "Name",  # Field identifier
    "Type",  # Data type
    "Value",  # Field content
}


# Required properties for array elements per OGWS-1.txt
REQUIRED_ELEMENT_PROPERTIES: Final[Set[str]] = {
    "Index",  # Zero-based array position
    "Fields",  # Element field container
}
