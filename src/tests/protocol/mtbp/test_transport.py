"""Tests for MTBP transport layer implementation.

This module contains tests that verify the transport layer functionality
including connection state management and message handling.
"""

import pytest

from protocols.mtbp.transport.connection import (
    ConnectionState,
    MessageType,
    MTBPConnection,
)
from protocols.mtbp.validation.exceptions import ProtocolError


class TestMTBPTransport:
    """Test suite for MTBP transport layer implementation."""

    connection: MTBPConnection

    def setup_method(self):
        """Set up test environment before each test."""
        self.connection = MTBPConnection()

    def test_initial_state(self):
        """Test initial connection state."""
        assert self.connection.state == ConnectionState.DISCONNECTED

    def test_valid_state_transitions(self):
        """Test valid state transitions."""
        # DISCONNECTED -> CONNECTING
        self.connection.connect()
        assert self.connection.state == ConnectionState.CONNECTING

        # CONNECTING -> CONNECTED
        self.connection.handle_message(MessageType.ACK)
        assert self.connection.state == ConnectionState.CONNECTED

        # CONNECTED -> DISCONNECTING
        self.connection.disconnect()
        assert self.connection.state == ConnectionState.DISCONNECTING

        # DISCONNECTING -> DISCONNECTED
        self.connection.handle_message(MessageType.NACK)
        assert self.connection.state == ConnectionState.DISCONNECTED

    def test_invalid_state_transitions(self):
        """Test invalid state transitions raise appropriate errors."""
        # Cannot connect when already connecting
        self.connection.connect()
        with pytest.raises(ProtocolError) as exc_info:
            self.connection.connect()
        assert exc_info.value.error_code == ProtocolError.PROTOCOL_VIOLATION

        # Cannot send data when not connected
        with pytest.raises(ProtocolError) as exc_info:
            self.connection.send_data()
        assert exc_info.value.error_code == ProtocolError.PROTOCOL_VIOLATION

        # Cannot disconnect when already disconnected
        self.connection = MTBPConnection()  # Reset to DISCONNECTED
        with pytest.raises(ProtocolError) as exc_info:
            self.connection.disconnect()
        assert exc_info.value.error_code == ProtocolError.PROTOCOL_VIOLATION

    def test_data_handling(self):
        """Test data handling in connected state."""
        # Connect first
        self.connection.connect()
        self.connection.handle_message(MessageType.ACK)
        assert self.connection.state == ConnectionState.CONNECTED

        # Send data
        self.connection.send_data()
        assert self.connection.state == ConnectionState.CONNECTED

        # Receive ACK
        self.connection.handle_message(MessageType.ACK)
        assert self.connection.state == ConnectionState.CONNECTED

    def test_state_callbacks(self):
        """Test state change callbacks."""
        callback_called = False

        def on_connected():
            nonlocal callback_called
            callback_called = True

        # Register callback for CONNECTED state
        self.connection.register_callback(ConnectionState.CONNECTED, on_connected)

        # Trigger connection
        self.connection.connect()
        self.connection.handle_message(MessageType.ACK)

        # Verify callback was called
        assert callback_called

    def test_connection_lifecycle(self):
        """Test complete connection lifecycle."""
        states = []

        def state_callback():
            states.append(self.connection.state)

        # Register callback for all states
        for state in ConnectionState:
            self.connection.register_callback(state, state_callback)

        # Complete connection lifecycle
        self.connection.connect()  # DISCONNECTED -> CONNECTING
        self.connection.handle_message(MessageType.ACK)  # -> CONNECTED
        self.connection.send_data()  # Stays CONNECTED
        self.connection.handle_message(MessageType.ACK)  # Stays CONNECTED
        self.connection.disconnect()  # -> DISCONNECTING
        self.connection.handle_message(MessageType.NACK)  # -> DISCONNECTED

        # Verify state sequence
        expected_states = [
            ConnectionState.CONNECTING,
            ConnectionState.CONNECTED,
            ConnectionState.CONNECTED,
            ConnectionState.CONNECTED,
            ConnectionState.DISCONNECTING,
            ConnectionState.DISCONNECTED,
        ]
        assert states == expected_states
