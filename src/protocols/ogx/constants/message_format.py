"""Constants for message format as defined in OGWS-1.txt.

This module defines the required fields and properties for messages:

Message Direction:
- Indicates whether a message is to-mobile (forward) or from-mobile (return)
- Used to determine message flow and validation rules
- Affects required fields and validation requirements

Error State Handling:
    Validation Errors:
    1. Field Format Errors:
       - Invalid field type
       - Missing required field
       - Value out of range
       - Invalid enum value
       Recovery: Client must correct and resubmit

    2. Content Validation Errors:
       - Invalid UTF-8 encoding
       - Malformed JSON structure
       - Array index gaps
       - Duplicate field names
       Recovery: Client must fix content format

    3. Size Validation Errors:
       - Message too large
       - Field count exceeds limit
       - Array size exceeds limit
       - String length exceeds limit
       Recovery: Client must reduce content size

    4. Semantic Validation Errors:
       - Invalid field combinations
       - Conditional field missing
       - Incompatible field values
       - Invalid state transitions
       Recovery: Client must correct business logic

Error Recovery Procedures:
    1. Immediate Rejection:
       - Format errors
       - Size violations
       - Missing required fields
       Action: Return 400 with details

    2. Partial Processing:
       - Valid fields processed
       - Invalid fields marked
       - Warning flags set
       Action: Return 207 with details

    3. Delayed Validation:
       - Network-specific rules
       - Terminal capability check
       - Resource availability
       Action: Accept but may fail later

    4. Validation Bypass:
       - Emergency messages
       - System maintenance
       - Debug/testing mode
       Action: Log warning and process

Required Fields:
- Mandatory fields that must be present in every message
- Includes message identifiers and payload containers
- Missing fields cause validation errors

Required Properties:
- Mandatory properties for fields and elements
- Ensures proper message structure and validation
- Properties must have non-None values

Usage:
    from protocols.ogx.constants import (
        MessageDirection,
        REQUIRED_MESSAGE_FIELDS,
        REQUIRED_FIELD_PROPERTIES,
        REQUIRED_ELEMENT_PROPERTIES
    )

    # Validate message structure with enhanced error handling
    def validate_message(message: dict) -> tuple[bool, list[str]]:
        errors = []
        warnings = []

        # Check required fields with detailed error context
        for field in REQUIRED_MESSAGE_FIELDS:
            if field not in message:
                errors.append({
                    "code": "MISSING_FIELD",
                    "field": field,
                    "severity": "ERROR",
                    "message": f"Required field missing: {field}"
                })
            elif message[field] is None:
                errors.append({
                    "code": "NULL_FIELD",
                    "field": field,
                    "severity": "ERROR",
                    "message": f"Required field cannot be None: {field}"
                })

        # Validate field properties with type checking
        for field in message.get("Fields", []):
            try:
                validate_field_properties(field)
            except ValidationError as e:
                errors.append({
                    "code": "INVALID_FIELD",
                    "field": field.get("Name", "unknown"),
                    "severity": "ERROR",
                    "message": str(e)
                })

        # Check message direction specific rules
        if message.get("direction") == MessageDirection.TO_MOBILE:
            validate_forward_message(message, errors, warnings)
        else:
            validate_return_message(message, errors, warnings)

        return not errors, {"errors": errors, "warnings": warnings}

    # Enhanced field validation with detailed error reporting
    def validate_field_properties(field: dict) -> None:
        for prop in REQUIRED_FIELD_PROPERTIES:
            if prop not in field:
                raise ValidationError({
                    "code": "MISSING_PROPERTY",
                    "property": prop,
                    "message": f"Missing required property: {prop}"
                })
            if field[prop] is None:
                raise ValidationError({
                    "code": "NULL_PROPERTY",
                    "property": prop,
                    "message": f"Required property cannot be None: {prop}"
                })

        # Type-specific validation
        validate_field_type(field["Type"], field["Value"])

    # Validate array elements with index checking
    def validate_element(element: dict) -> None:
        for prop in REQUIRED_ELEMENT_PROPERTIES:
            if prop not in element:
                raise ValidationError({
                    "code": "MISSING_ELEMENT_PROPERTY",
                    "property": prop,
                    "message": f"Missing required element property: {prop}"
                })
            if element[prop] is None:
                raise ValidationError({
                    "code": "NULL_ELEMENT_PROPERTY",
                    "property": prop,
                    "message": f"Required element property cannot be None: {prop}"
                })

        # Validate element index sequence
        if not isinstance(element["Index"], int) or element["Index"] < 0:
            raise ValidationError({
                "code": "INVALID_INDEX",
                "index": element["Index"],
                "message": "Element index must be non-negative integer"
            })

Implementation Notes:
    - All required fields/properties must be present and non-None
    - Field names are case-sensitive
    - Order of fields is preserved during encoding/decoding
    - Additional fields beyond required ones are allowed
    - Validation should occur before encoding/after decoding
    - Some fields are only valid for specific message directions
    - Field types must match their declared types
    - Array elements must have sequential indices
    - Property fields require type attribute
    - Error handling includes detailed context
    - Validation can be partial or complete
    - Some errors are recoverable
    - Error reporting includes severity levels
"""

from enum import Enum
from typing import Final, Set


class MessageDirection(str, Enum):
    """Message direction as defined in OGWS-1.txt.

    Determines the flow of messages between gateway and terminals:
    - TO_MOBILE: Forward messages sent from gateway to terminal
    - FROM_MOBILE: Return messages sent from terminal to gateway

    Direction affects message validation and processing rules.

    Usage:
        # Create new message
        def create_message(data: dict, to_terminal: bool) -> dict:
            direction = (
                MessageDirection.TO_MOBILE if to_terminal
                else MessageDirection.FROM_MOBILE
            )
            return {
                "direction": direction,
                "payload": data,
                "timestamp": get_timestamp()
            }

        # Route message
        def route_message(message: dict) -> None:
            if message["direction"] == MessageDirection.TO_MOBILE:
                validate_destination(message["terminal_id"])
                send_to_terminal(message)
            else:
                validate_source(message["terminal_id"])
                deliver_to_client(message)

        # Get required fields
        def get_required_fields(direction: MessageDirection) -> set[str]:
            base_fields = REQUIRED_MESSAGE_FIELDS.copy()
            if direction == MessageDirection.TO_MOBILE:
                base_fields.add("terminal_id")
            return base_fields

    Implementation Notes:
        - Direction determines required message fields
        - TO_MOBILE requires valid destination terminal ID
        - FROM_MOBILE includes source terminal ID
        - Validation rules vary by message direction
        - Some features only available for specific directions
        - Direction affects message routing and handling
        - Field requirements differ by direction
        - Error handling varies by direction
    """

    TO_MOBILE = "to-mobile"  # Forward message - sent to terminal
    FROM_MOBILE = "from-mobile"  # Return message - from terminal


# Required fields for every message
REQUIRED_MESSAGE_FIELDS: Final[Set[str]] = {
    "MIN",  # Message identification number
    "SIN",  # Service identification number
    "Name",  # Message name
    "Fields",  # Array of Field instances
}
"""Required fields that must be present in every message.

These fields are mandatory according to OGWS-1.txt:
- MIN: Message identification number within service (1-255)
- SIN: Service identification number (16-255)
- Name: Human-readable message name
- Fields: Container for message payload fields

Usage:
    # Validate message structure
    def validate_message(message: dict) -> None:
        for field in REQUIRED_MESSAGE_FIELDS:
            if field not in message:
                raise ValidationError(f"Missing required field: {field}")
            if message[field] is None:
                raise ValidationError(f"Required field cannot be None: {field}")

        # Validate field values
        if not (16 <= message["SIN"] <= 255):
            raise ValidationError("SIN must be between 16 and 255")
        if not (1 <= message["MIN"] <= 255):
            raise ValidationError("MIN must be between 1 and 255")
        if not isinstance(message["Fields"], list):
            raise ValidationError("Fields must be a list")

Implementation Notes:
    - Fields must be present and non-None
    - SIN/MIN have valid ranges
    - Name must be a string
    - Fields must be a list
    - Order matters for some fields
    - Additional fields allowed
    - Case-sensitive field names
"""


# Required properties for every field
REQUIRED_FIELD_PROPERTIES: Final[Set[str]] = {
    "Name",  # Field name
    "Type",  # Type of the field
    "Value",  # Value of the field
}
"""Required properties that must be present in every field.

These properties are mandatory according to OGWS-1.txt:
- Name: Identifier for the field
- Type: Data type (see FieldType enum)
- Value: Field content

Usage:
    # Validate field structure
    def validate_field(field: dict) -> None:
        for prop in REQUIRED_FIELD_PROPERTIES:
            if prop not in field:
                raise ValidationError(f"Missing required property: {prop}")
            if field[prop] is None:
                raise ValidationError(f"Required property cannot be None: {prop}")

        # Additional validation
        if not isinstance(field["Name"], str):
            raise ValidationError("Name must be a string")
        if field["Type"] not in FieldType:
            raise ValidationError(f"Invalid field type: {field['Type']}")
        validate_field_value(field["Type"], field["Value"])

Implementation Notes:
    - Properties must be present and non-None
    - Name must be unique within message
    - Type must be valid FieldType
    - Value must match Type
    - Case-sensitive properties
    - Order preservation important
    - Type validation strict
"""


# Required properties for every element
REQUIRED_ELEMENT_PROPERTIES: Final[Set[str]] = {
    "Index",  # Element's index
    "Fields",  # Element's fields
}
"""Required properties that must be present in every element.

These properties are mandatory according to OGWS-1.txt:
- Index: Position in the array (0-based integer)
- Fields: Container for element fields (list of Field objects)

Usage:
    # Validate element structure
    def validate_element(element: dict) -> None:
        for prop in REQUIRED_ELEMENT_PROPERTIES:
            if prop not in element:
                raise ValidationError(f"Missing required property: {prop}")
            if element[prop] is None:
                raise ValidationError(f"Required property cannot be None: {prop}")

        # Additional validation
        if not isinstance(element["Index"], int) or element["Index"] < 0:
            raise ValidationError("Index must be non-negative integer")
        if not isinstance(element["Fields"], list):
            raise ValidationError("Fields must be a list")

Implementation Notes:
    - Properties must be present and non-None
    - Index must be sequential
    - Fields must be a list
    - Element order matters
    - Case-sensitive properties
    - No gaps in indices
    - Fields inherit parent type
"""
