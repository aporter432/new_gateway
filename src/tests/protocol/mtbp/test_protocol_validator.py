"""Tests for MTBP protocol validator implementation.

This module contains tests that verify the protocol validator functionality
according to N210 IGWS2 specification.
"""

import pytest

from protocols.mtbp.constants.message_types import MessageType
from protocols.mtbp.models.messages import MTBPMessage
from protocols.mtbp.validation.validators.protocol_validator import MTBPProtocolValidator
from protocols.mtbp.validation.exceptions import ProtocolError


class TestMTBPProtocolValidator:
    """Test suite for MTBP protocol validator implementation."""

    validator: MTBPProtocolValidator

    def setup_method(self):
        """Set up test environment before each test."""
        self.validator = MTBPProtocolValidator()

    def _reset_validator(self) -> MTBPProtocolValidator:
        """Helper method to get a fresh validator instance."""
        self.validator = MTBPProtocolValidator()
        return self.validator

    def test_sequence_number_range(self):
        """Test sequence number range validation."""
        # Create alternating DATA and ACK messages for valid transitions
        data_msg = MTBPMessage(sin=1, min_id=1, message_type=MessageType.DATA, is_forward=True)
        ack_msg = MTBPMessage(sin=1, min_id=1, message_type=MessageType.ACK, is_forward=False)

        # Valid sequence numbers
        self.validator.validate(data_msg, sequence_number=0)  # Min
        self.validator.validate(ack_msg, sequence_number=65535)  # Max

        # Invalid sequence numbers
        with pytest.raises(ProtocolError) as exc_info:
            self.validator.validate(data_msg, sequence_number=-1)  # Below min
        assert exc_info.value.error_code == ProtocolError.SEQUENCE_ERROR

        with pytest.raises(ProtocolError) as exc_info:
            self.validator.validate(ack_msg, sequence_number=65536)  # Above max
        assert exc_info.value.error_code == ProtocolError.SEQUENCE_ERROR

    def test_sequence_ordering(self):
        """Test sequence number ordering validation."""
        # Create alternating DATA and ACK messages for valid transitions
        data_msg = MTBPMessage(sin=1, min_id=1, message_type=MessageType.DATA, is_forward=True)
        ack_msg = MTBPMessage(sin=1, min_id=1, message_type=MessageType.ACK, is_forward=False)

        # Sequential messages should pass
        self.validator.validate(data_msg, sequence_number=1)
        self.validator.validate(ack_msg, sequence_number=2)
        self.validator.validate(data_msg, sequence_number=3)

        # Duplicate sequence should fail
        with pytest.raises(ProtocolError) as exc_info:
            self.validator.validate(ack_msg, sequence_number=2)  # Already used
        assert exc_info.value.error_code == ProtocolError.SEQUENCE_ERROR

    def test_sequence_wrapping(self):
        """Test sequence number wrapping at MAX_SEQUENCE_NUMBER."""
        # Create alternating DATA and ACK messages for valid transitions
        data_msg = MTBPMessage(sin=1, min_id=1, message_type=MessageType.DATA, is_forward=True)
        ack_msg = MTBPMessage(sin=1, min_id=1, message_type=MessageType.ACK, is_forward=False)

        # Test wrapping at max value
        self.validator.validate(data_msg, sequence_number=65534)
        self.validator.validate(ack_msg, sequence_number=65535)
        self.validator.validate(data_msg, sequence_number=0)  # Should wrap to 0
        self.validator.validate(ack_msg, sequence_number=1)

        # Test invalid wrapping (too early)
        self._reset_validator()  # Reset validator
        self.validator.validate(data_msg, sequence_number=1000)
        with pytest.raises(ProtocolError) as exc_info:
            self.validator.validate(ack_msg, sequence_number=0)  # Shouldn't wrap yet
        assert exc_info.value.error_code == ProtocolError.SEQUENCE_ERROR

    def test_out_of_order_messages(self):
        """Test handling of out-of-order messages."""
        # Create alternating DATA and ACK messages for valid transitions
        data_msg = MTBPMessage(sin=1, min_id=1, message_type=MessageType.DATA, is_forward=True)
        ack_msg = MTBPMessage(sin=1, min_id=1, message_type=MessageType.ACK, is_forward=False)

        # Test within MAX_OUT_OF_ORDER limit
        for i in range(0, self.validator.MAX_OUT_OF_ORDER, 2):
            if i % 4 == 0:
                self.validator.validate(data_msg, sequence_number=i)
            else:
                self.validator.validate(ack_msg, sequence_number=i)

        # Test exceeding MAX_OUT_OF_ORDER
        self._reset_validator()
        with pytest.raises(ProtocolError) as exc_info:
            for i in range(self.validator.MAX_OUT_OF_ORDER + 1):
                if i % 2 == 0:
                    self.validator.validate(data_msg, sequence_number=i * 2)
                else:
                    self.validator.validate(ack_msg, sequence_number=i * 2)
        assert exc_info.value.error_code == ProtocolError.SEQUENCE_ERROR

    def test_message_type_transitions(self):
        """Test message type transition validation."""
        # Test DATA -> ACK/NACK
        self.validator.validate(
            MTBPMessage(sin=1, min_id=1, message_type=MessageType.DATA, is_forward=True),
            sequence_number=1,
        )
        self.validator.validate(
            MTBPMessage(sin=1, min_id=1, message_type=MessageType.ACK, is_forward=False),
            sequence_number=2,
        )

        # Test CONTROL -> ACK/NACK
        self._reset_validator()  # Reset validator
        self.validator.validate(
            MTBPMessage(sin=1, min_id=1, message_type=MessageType.CONTROL, is_forward=True),
            sequence_number=1,
        )
        self.validator.validate(
            MTBPMessage(sin=1, min_id=1, message_type=MessageType.NACK, is_forward=False),
            sequence_number=2,
        )

        # Test ACK -> DATA/CONTROL
        self._reset_validator()  # Reset validator
        self.validator.validate(
            MTBPMessage(sin=1, min_id=1, message_type=MessageType.ACK, is_forward=False),
            sequence_number=1,
        )
        self.validator.validate(
            MTBPMessage(sin=1, min_id=1, message_type=MessageType.DATA, is_forward=True),
            sequence_number=2,
        )

        # Test invalid transitions
        self._reset_validator()  # Reset validator
        self.validator.validate(
            MTBPMessage(sin=1, min_id=1, message_type=MessageType.DATA, is_forward=True),
            sequence_number=1,
        )
        with pytest.raises(ProtocolError) as exc_info:
            self.validator.validate(
                MTBPMessage(sin=1, min_id=1, message_type=MessageType.DATA, is_forward=True),
                sequence_number=2,  # DATA -> DATA not allowed
            )
        assert exc_info.value.error_code == ProtocolError.PROTOCOL_VIOLATION

    def test_first_message_type(self):
        """Test that first message can be any type."""
        # All message types should be valid as first message
        for msg_type in MessageType:
            self._reset_validator()  # Fresh validator for each test
            self.validator.validate(
                MTBPMessage(sin=1, min_id=1, message_type=msg_type, is_forward=True),
                sequence_number=1,
            )

    def test_reset_sequence(self):
        """Test sequence number tracking reset."""
        # Create alternating DATA and ACK messages for valid transitions
        data_msg = MTBPMessage(sin=1, min_id=1, message_type=MessageType.DATA, is_forward=True)
        ack_msg = MTBPMessage(sin=1, min_id=1, message_type=MessageType.ACK, is_forward=False)

        # Use some sequence numbers
        self.validator.validate(data_msg, sequence_number=1)
        self.validator.validate(ack_msg, sequence_number=2)

        # Reset tracking
        self.validator.reset_sequence()

        # Should be able to reuse sequence numbers
        self.validator.validate(data_msg, sequence_number=1)
        self.validator.validate(ack_msg, sequence_number=2)
