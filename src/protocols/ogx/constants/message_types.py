"""Message types as defined in N214 section 5.1.

This module defines the direction of message flow between gateway and terminals.
Message types determine:
- Message validation rules
- Required fields and properties
- Processing and routing behavior

Usage:
    from protocols.ogx.constants import MessageType

    # Validate message based on type
    def validate_message(message: dict) -> None:
        if message["type"] == MessageType.TO_MOBILE:
            validate_forward_message_fields(message)
            check_destination_terminal(message["terminal_id"])
        else:
            validate_return_message_fields(message)
            check_source_terminal(message["terminal_id"])

    # Route message based on type
    def route_message(message: dict) -> None:
        if message["type"] == MessageType.TO_MOBILE:
            send_to_terminal(message)
        else:
            deliver_to_client(message)

Implementation Notes:
    - TO_MOBILE messages require valid destination terminal
    - FROM_MOBILE messages include source terminal info
    - Message type affects field validation rules
    - Some fields only valid for specific message types
    - Type determines message flow through system
"""

from enum import Enum


class MessageType(str, Enum):
    """Message types for gateway communication.

    Defines message flow direction:
    - TO_MOBILE: Forward messages from gateway to terminal
    - FROM_MOBILE: Return messages from terminal to gateway

    Usage:
        # Create new message
        def create_message(data: dict, to_terminal: bool) -> dict:
            msg_type = (
                MessageType.TO_MOBILE if to_terminal
                else MessageType.FROM_MOBILE
            )
            return {
                "type": msg_type,
                "payload": data,
                "timestamp": get_timestamp()
            }

    Implementation Notes:
        - Type determines required message fields
        - TO_MOBILE requires destination terminal ID
        - FROM_MOBILE includes source terminal ID
        - Validation rules vary by message type
        - Some features only available for specific types
    """

    TO_MOBILE = "to-mobile"  # Forward messages to terminal
    FROM_MOBILE = "from-mobile"  # Return messages from terminal
