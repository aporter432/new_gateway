"""Fixtures for OGx protocol validation tests."""

import pytest

from protocols.ogx.constants import FieldType, MessageType, NetworkType
from protocols.ogx.models.fields import Element, Field, Message
from protocols.ogx.validation.common.types import ValidationContext
from protocols.ogx.validation.message.field_validator import OGxFieldValidator


@pytest.fixture
def field_validator() -> OGxFieldValidator:
    """Provide configured field validator."""
    return OGxFieldValidator()


@pytest.fixture
def context() -> ValidationContext:
    """Provide test validation context."""
    return ValidationContext(network_type=NetworkType.OGX, direction=MessageType.FORWARD)


@pytest.fixture
def simple_message():
    """Create a simple OGx message with basic fields."""
    fields = [
        Field(name="string_field", type=FieldType.STRING, value="test"),
        Field(name="int_field", type=FieldType.SIGNED_INT, value=42),
    ]
    return Message(name="test_message", sin=16, min=1, fields=fields)


@pytest.fixture
def complex_message():
    """Create a complex OGx message with nested structures."""
    fields = [
        Field(name="string_field", type=FieldType.STRING, value="test"),
        Field(name="int_field", type=FieldType.SIGNED_INT, value=-42),
        Field(
            name="array_field",
            type=FieldType.ARRAY,
            elements=[
                Element(
                    index=0,
                    fields=[Field(name="sub_field", type=FieldType.BOOLEAN, value=True)],
                )
            ],
        ),
    ]
    return Message(name="complex_test", sin=16, min=1, fields=fields)


@pytest.fixture
def edge_case_fields():
    """Create a list of fields with edge case values."""
    return [
        Field(name="max_uint", type=FieldType.UNSIGNED_INT, value=2**32 - 1),
        Field(name="min_int", type=FieldType.SIGNED_INT, value=-(2**31)),
        Field(name="bool_field", type=FieldType.BOOLEAN, value=True),
        Field(name="empty_string", type=FieldType.STRING, value=""),
        Field(name="unicode_string", type=FieldType.STRING, value="Hello 世界 🌍"),
        Field(name="enum_field", type=FieldType.ENUM, value="OPTION_A"),
    ]
