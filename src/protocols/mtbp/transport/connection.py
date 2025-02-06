"""MTBP Transport Layer Connection Management

This module implements connection state management for MTBP transport layer
according to N210 IGWS2 specification.
"""

from enum import Enum, auto
from typing import Callable, Dict

from ..constants.message_types import MessageType
from ..validation.exceptions import ProtocolError


class ConnectionState(Enum):
    """Connection states for MTBP transport layer"""

    DISCONNECTED = auto()
    CONNECTING = auto()
    CONNECTED = auto()
    DISCONNECTING = auto()


class MTBPConnection:
    """Manages MTBP transport layer connection state"""

    # Valid state transitions
    _VALID_TRANSITIONS = {
        ConnectionState.DISCONNECTED: {MessageType.DATA: ConnectionState.CONNECTING},
        ConnectionState.CONNECTING: {
            MessageType.ACK: ConnectionState.CONNECTED,
            MessageType.NACK: ConnectionState.DISCONNECTING,
        },
        ConnectionState.CONNECTED: {
            MessageType.CONTROL: ConnectionState.DISCONNECTING,
            MessageType.DATA: ConnectionState.CONNECTED,
            MessageType.ACK: ConnectionState.CONNECTED,
        },
        ConnectionState.DISCONNECTING: {MessageType.NACK: ConnectionState.DISCONNECTED},
    }

    def __init__(self):
        """Initialize connection in DISCONNECTED state"""
        self._state = ConnectionState.DISCONNECTED
        self._callbacks: Dict[ConnectionState, Callable] = {}

    @property
    def state(self) -> ConnectionState:
        """Get current connection state"""
        return self._state

    def register_callback(self, state: ConnectionState, callback: Callable) -> None:
        """Register callback for state change notification"""
        self._callbacks[state] = callback

    def handle_message(self, message_type: MessageType) -> None:
        """
        Handle incoming message and update state accordingly.

        Args:
            message_type: Type of message received

        Raises:
            ProtocolError: If message type is invalid for current state
        """
        # Get valid transitions for current state
        valid_transitions = self._VALID_TRANSITIONS.get(self._state, {})

        # Check if message type is valid for current state
        if message_type not in valid_transitions:
            raise ProtocolError(
                f"Invalid message type {message_type} for state {self._state}",
                error_code=ProtocolError.PROTOCOL_VIOLATION,
            )

        # Update state
        new_state = valid_transitions[message_type]
        self._state = new_state

        # Notify callback if registered
        if new_state in self._callbacks:
            self._callbacks[new_state]()

    def connect(self) -> None:
        """Initiate connection"""
        if self._state != ConnectionState.DISCONNECTED:
            raise ProtocolError(
                f"Cannot connect from state {self._state}",
                error_code=ProtocolError.PROTOCOL_VIOLATION,
            )
        self.handle_message(MessageType.DATA)

    def disconnect(self) -> None:
        """Initiate disconnection"""
        if self._state not in (ConnectionState.CONNECTED, ConnectionState.CONNECTING):
            raise ProtocolError(
                f"Cannot disconnect from state {self._state}",
                error_code=ProtocolError.PROTOCOL_VIOLATION,
            )
        self.handle_message(MessageType.CONTROL)

    def send_data(self) -> None:
        """
        Send data over connection.

        Raises:
            ProtocolError: If connection is not in CONNECTED state
        """
        if self._state != ConnectionState.CONNECTED:
            raise ProtocolError(
                f"Cannot send data in state {self._state}",
                error_code=ProtocolError.PROTOCOL_VIOLATION,
            )
        self.handle_message(MessageType.DATA)
