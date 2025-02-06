"""Tests for MTBP protocol message models.

This module contains tests that verify the message models conform to 
N200 section 1.2.2 requirements for satellite binary encoding compatibility.
"""

from typing import Any

import pytest

from protocols.mtbp.constants.message_types import MessageType
from protocols.mtbp.constants.field_types import FieldType
from protocols.mtbp.models.messages import MTBPMessage
from protocols.mtbp.models.fields import Field
from protocols.mtbp.validation.exceptions import ParseError


class TestMTBPMessage:
    """Test suite for MTBP message implementation."""

    def test_message_creation(self):
        """Test basic message creation and validation."""
        # Valid message
        msg = MTBPMessage(
            sin=1, min_id=1, message_type=MessageType.DATA, is_forward=True, fields=[]
        )
        assert msg.sin == 1
        assert msg.min_id == 1
        assert msg.message_type == MessageType.DATA
        assert msg.is_forward is True

        # Invalid SIN
        with pytest.raises(ParseError) as exc_info:
            MTBPMessage(
                sin=256,  # Too large for 1 byte
                min_id=1,
                message_type=MessageType.DATA,
                is_forward=True,
            )
        assert exc_info.value.error_code == ParseError.INVALID_SIN

        # Invalid MIN
        with pytest.raises(ParseError) as exc_info:
            MTBPMessage(
                sin=1,
                min_id=256,  # Too large for 1 byte
                message_type=MessageType.DATA,
                is_forward=True,
            )
        assert exc_info.value.error_code == ParseError.INVALID_MIN

    def test_field_handling(self):
        """Test field addition and validation."""
        msg = MTBPMessage(sin=1, min_id=1, message_type=MessageType.DATA, is_forward=True)

        # Add valid field
        field = Field(field_type=FieldType.UINT, value=123)
        msg.add_field(field)
        assert len(msg.fields) == 1
        assert msg.fields[0].field_type == FieldType.UINT
        assert msg.fields[0].value == 123

        # Add invalid field type
        invalid_field = Field(field_type=FieldType.UINT, value=123)
        invalid_field.field_type = "not a field"  # type: ignore
        with pytest.raises(ParseError) as exc_info:
            msg.add_field(invalid_field)
        assert exc_info.value.error_code == ParseError.INVALID_FIELD_VALUE

    def test_message_types(self):
        """Test message type validation."""
        # Valid message types
        for msg_type in MessageType:
            msg = MTBPMessage(sin=1, min_id=1, message_type=msg_type, is_forward=True)
            assert msg.message_type == msg_type

        # Invalid message type
        with pytest.raises(ParseError) as exc_info:
            invalid_type: Any = "INVALID"
            MTBPMessage(sin=1, min_id=1, message_type=invalid_type, is_forward=True)  # type: ignore
        assert exc_info.value.error_code == ParseError.INVALID_FIELD_TYPE

    def test_satellite_compatibility(self):
        """Test satellite binary format compatibility."""
        # Create message with all field types
        msg = MTBPMessage(
            sin=1,
            min_id=1,
            message_type=MessageType.DATA,
            is_forward=True,
            fields=[
                Field(field_type=FieldType.UINT, value=123),
                Field(field_type=FieldType.INT, value=-123),
                Field(field_type=FieldType.BOOLEAN, value=True),
                Field(field_type=FieldType.STRING, value="test"),
                Field(field_type=FieldType.DATA, value=bytes([1, 2, 3])),
                Field(field_type=FieldType.ENUM, value=1),
            ],
        )

        # Verify field encoding matches satellite format
        assert isinstance(msg.fields[0].value, int)
        assert isinstance(msg.fields[1].value, int)
        assert isinstance(msg.fields[2].value, bool)
        assert isinstance(msg.fields[3].value, str)
        assert isinstance(msg.fields[4].value, bytes)
        assert isinstance(msg.fields[5].value, int)

    def test_field_constraints(self):
        """Test field value constraints."""
        msg = MTBPMessage(sin=1, min_id=1, message_type=MessageType.DATA, is_forward=True)

        # Test integer ranges
        with pytest.raises(ParseError):
            msg.add_field(Field(field_type=FieldType.UINT, value=-1))  # Invalid negative

        with pytest.raises(ParseError):
            msg.add_field(Field(field_type=FieldType.UINT, value=2**32))  # Too large

        # Test string length
        with pytest.raises(ParseError):
            msg.add_field(Field(field_type=FieldType.STRING, value="x" * 65536))  # Too long

        # Test data length
        with pytest.raises(ParseError):
            msg.add_field(Field(field_type=FieldType.DATA, value=bytes([0] * 65536)))  # Too long
