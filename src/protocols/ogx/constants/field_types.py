"""Field types as defined in OGWS-1.txt section 5.1.

This module defines the field types for OGWS message payloads.

Field Types (from OGWS-1.txt Table 3):
- Enum: Enumeration value
- Boolean: True or False
- Unsigned Int: Decimal number (non-negative)
- Signed Int: Decimal number (including negative)
- String: Text string
- Data: Base64 encoded data
- Array: List of elements
- Message: Nested message
- Dynamic: Runtime resolved type
- Property: Configuration property

OGWS API Usage Examples:

    # Example 1: Submit message with various field types
    # POST https://ogws.orbcomm.com/api/v1.0/submit/messages
    submit_request = {
        "DestinationID": "01008988SKY5909",
        "Payload": {
            "Name": "sensorReadings",
            "SIN": 128,
            "MIN": 1,
            "Fields": [
                {
                    "Name": "temperature",
                    "Type": FieldType.SIGNED_INT,
                    "Value": "-15"
                },
                {
                    "Name": "doorOpen",
                    "Type": FieldType.BOOLEAN,
                    "Value": "True"
                },
                {
                    "Name": "status",
                    "Type": FieldType.ENUM,
                    "Value": "active"
                }
            ]
        }
    }

    # Example 2: Message with array elements
    # GET https://ogws.orbcomm.com/api/v1.0/get/re_messages
    message_response = {
        "ID": 10844864715,
        "Payload": {
            "Name": "locationHistory",
            "SIN": 128,
            "MIN": 2,
            "Fields": [{
                "Name": "positions",
                "Type": FieldType.ARRAY,
                "Elements": [
                    {
                        "Index": 0,
                        "Fields": [
                            {
                                "Name": "latitude",
                                "Type": FieldType.SIGNED_INT,
                                "Value": "4534590"
                            }
                        ]
                    }
                ]
            }]
        }
    }

    # Example 3: Raw binary data field
    raw_message = {
        "Name": "firmware",
        "SIN": 128,
        "MIN": 3,
        "Fields": [{
            "Name": "data",
            "Type": FieldType.DATA,
            "Value": "YQECAxY="  # Base64 encoded
        }]
    }

Implementation Notes from OGWS-1.txt:
    - Field types determine payload encoding/decoding
    - String values must be UTF-8 encoded
    - Boolean accepts "True"/"False" or "1"/"0"
    - Integer ranges are enforced by network
    - Enum values must be predefined
    - Data fields must be base64 encoded
    - Array elements must have sequential indices
    - Message fields support nested structures
    - Dynamic types resolved at runtime
    - Property fields require type attribute
"""

from enum import Enum


class FieldType(str, Enum):
    """Field types as defined in OGWS-1.txt Table 3.

    Attributes:
        ENUM: Enumeration value from predefined set
        BOOLEAN: True/False value ("True"/"False" or "1"/"0")
        UNSIGNED_INT: Non-negative decimal number
        SIGNED_INT: Decimal number (including negative)
        STRING: UTF-8 encoded text string
        DATA: Base64 encoded binary data
        ARRAY: Sequence of elements
        MESSAGE: Nested message structure
        DYNAMIC: Type determined at runtime
        PROPERTY: Configuration property field

    API Usage Example:
        # Message payload with multiple field types
        {
            "Name": "deviceStatus",
            "SIN": 128,
            "MIN": 1,
            "Fields": [
                {
                    "Name": "batteryLevel",
                    "Type": FieldType.UNSIGNED_INT,
                    "Value": "95"
                },
                {
                    "Name": "temperature",
                    "Type": FieldType.SIGNED_INT,
                    "Value": "-10"
                },
                {
                    "Name": "mode",
                    "Type": FieldType.ENUM,
                    "Value": "active"
                }
            ]
        }
    """

    ENUM = "enum"
    BOOLEAN = "boolean"
    UNSIGNED_INT = "unsignedint"
    SIGNED_INT = "signedint"
    STRING = "string"
    DATA = "data"
    ARRAY = "array"
    MESSAGE = "message"
    DYNAMIC = "dynamic"
    PROPERTY = "property"
