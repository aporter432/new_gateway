"""Tests for MTBP protocol implementation integration.

This module contains integration tests that verify the MTBP protocol components
work together correctly according to N210 requirements.
"""

import pytest

from protocols.mtbp.models.messages import MTBPMessage
from protocols.mtbp.models.fields import Field
from protocols.mtbp.constants.message_types import MessageType
from protocols.mtbp.constants.field_types import FieldType
from protocols.mtbp.models.serialization.message_serializer import MTBPMessageSerializer
from protocols.mtbp.validation.validators.protocol_validator import MTBPProtocolValidator
from protocols.mtbp.validation.exceptions import ProtocolError


class TestMTBPIntegration:
    """Integration test suite for MTBP protocol implementation."""

    def __init__(self):
        """Initialize test attributes."""
        self.validator = MTBPProtocolValidator()

    def setup_method(self) -> None:
        """Set up test environment before each test."""
        # Reset validator state if needed
        self.validator = MTBPProtocolValidator()

    def test_message_roundtrip(self):
        """Test full message roundtrip: create -> encode -> validate."""
        # Create original message
        original_msg = MTBPMessage(
            sin=1,
            min_id=1,
            message_type=MessageType.DATA,
            is_forward=True,
            fields=[
                Field(field_type=FieldType.UINT, value=123),
                Field(field_type=FieldType.STRING, value="test"),
                Field(field_type=FieldType.BOOLEAN, value=True),
            ],
        )

        # Convert to binary
        data = MTBPMessageSerializer.to_bytes(original_msg, sequence_number=1)

        # Parse back from binary
        parsed_msg, _, sequence = MTBPMessageSerializer.from_bytes(
            data, [FieldType.UINT, FieldType.STRING, FieldType.BOOLEAN]
        )

        # Validate parsed message
        self.validator.validate(parsed_msg, sequence_number=sequence)

        # Verify message preserved through roundtrip
        assert parsed_msg.sin == original_msg.sin
        assert parsed_msg.min_id == original_msg.min_id
        assert parsed_msg.message_type == original_msg.message_type
        assert parsed_msg.is_forward == original_msg.is_forward
        assert len(parsed_msg.fields) == len(original_msg.fields)

        for orig_field, parsed_field in zip(original_msg.fields, parsed_msg.fields):
            assert parsed_field.field_type == orig_field.field_type
            assert parsed_field.value == orig_field.value

    def test_protocol_sequence(self):
        """Test protocol message sequence validation."""
        # Create sequence of messages
        messages = [
            MTBPMessage(sin=1, min_id=1, message_type=MessageType.DATA, is_forward=True),
            MTBPMessage(sin=1, min_id=1, message_type=MessageType.ACK, is_forward=False),
            MTBPMessage(sin=1, min_id=1, message_type=MessageType.CONTROL, is_forward=True),
            MTBPMessage(sin=1, min_id=1, message_type=MessageType.NACK, is_forward=False),
        ]

        # Process sequence
        for i, msg in enumerate(messages, start=1):
            # Validate with incrementing sequence numbers
            self.validator.validate(msg, sequence_number=i)

    def test_error_handling(self):
        """Test error handling across components."""
        # Test invalid message type sequence
        messages = [
            MTBPMessage(sin=1, min_id=1, message_type=MessageType.DATA, is_forward=True),
            MTBPMessage(
                sin=1, min_id=1, message_type=MessageType.DATA, is_forward=True
            ),  # Invalid sequence
        ]

        # First message should pass
        self.validator.validate(messages[0], sequence_number=1)

        # Second message should fail validation
        with pytest.raises(ProtocolError) as exc_info:
            self.validator.validate(messages[1], sequence_number=2)
        assert exc_info.value.error_code == ProtocolError.PROTOCOL_VIOLATION

    def test_large_message_handling(self):
        """Test handling of messages approaching size limits."""
        # Create message with large field
        test_string = "x" * 1024
        test_bytes = bytes([0] * 1024)
        large_msg = MTBPMessage(
            sin=1,
            min_id=1,
            message_type=MessageType.DATA,
            is_forward=True,
            fields=[
                Field(field_type=FieldType.STRING, value=test_string),
                Field(field_type=FieldType.DATA, value=test_bytes),
            ],
        )

        # Verify roundtrip
        data = MTBPMessageSerializer.to_bytes(large_msg, sequence_number=1)
        parsed_msg, _, sequence = MTBPMessageSerializer.from_bytes(
            data, [FieldType.STRING, FieldType.DATA]
        )
        self.validator.validate(parsed_msg, sequence_number=sequence)

        # Verify field values preserved
        assert isinstance(parsed_msg.fields[0].value, str)
        assert isinstance(parsed_msg.fields[1].value, bytes)
        assert parsed_msg.fields[0].value == test_string
        assert parsed_msg.fields[1].value == test_bytes
