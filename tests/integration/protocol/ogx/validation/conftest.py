"""Test configuration and fixtures for protocol validation."""

import pytest

from Protexis_Command.protocol.ogx.constants import FieldType, MessageType, NetworkType
from Protexis_Command.protocol.ogx.models.fields import Element, Field, Message
from Protexis_Command.protocol.ogx.validation.validators.ogx_field_validator import (
    OGxFieldValidator,
)
from Protexis_Command.protocol.ogx.validation.validators.ogx_structure_validator import (
    OGxStructureValidator,
)
from Protexis_Command.protocol.ogx.validation.validators.ogx_type_validator import ValidationContext


@pytest.fixture
def field_validator() -> OGxFieldValidator:
    """Provide configured field validator."""
    return OGxFieldValidator()


@pytest.fixture
def validator() -> OGxStructureValidator:
    """Create a message validator instance."""
    return OGxStructureValidator()


@pytest.fixture
def context() -> ValidationContext:
    """Provide test validation context."""
    return ValidationContext(network_type=NetworkType.OGX, direction=MessageType.FORWARD)


@pytest.fixture
def simple_message():
    """Create a simple OGx message with basic fields."""
    fields = [
        Field(Name="string_field", Type=FieldType.STRING, Value="test"),
        Field(Name="int_field", Type=FieldType.SIGNED_INT, Value=42),
    ]
    return Message(Name="test_message", SIN=16, MIN=1, Fields=fields)


@pytest.fixture
def complex_message():
    """Create a complex OGx message with nested structures."""
    fields = [
        Field(Name="string_field", Type=FieldType.STRING, Value="test"),
        Field(Name="int_field", Type=FieldType.SIGNED_INT, Value=-42),
        Field(
            Name="array_field",
            Type=FieldType.ARRAY,
            Elements=[
                Element(
                    Index=0,
                    Fields=[Field(Name="sub_field", Type=FieldType.BOOLEAN, Value=True)],
                )
            ],
        ),
    ]
    return Message(Name="complex_test", SIN=16, MIN=1, Fields=fields)


@pytest.fixture
def edge_case_fields():
    """Create a list of fields with edge case values."""
    return [
        Field(Name="max_uint", Type=FieldType.UNSIGNED_INT, Value=2**32 - 1),
        Field(Name="min_int", Type=FieldType.SIGNED_INT, Value=-(2**31)),
        Field(Name="bool_field", Type=FieldType.BOOLEAN, Value=True),
        Field(Name="empty_string", Type=FieldType.STRING, Value=""),
        Field(Name="unicode_string", Type=FieldType.STRING, Value="Hello 世界 🌍"),
        Field(Name="enum_field", Type=FieldType.ENUM, Value="OPTION_A"),
    ]


@pytest.fixture
def nested_message():
    """Create a deeply nested message structure."""
    nested_fields = [
        # ... nested field structure ...
    ]
    return Message(Name="nested_test", SIN=16, MIN=1, Fields=nested_fields)


@pytest.fixture
def invalid_messages():
    """Create a collection of invalid message scenarios."""
    return {
        "missing_required": {
            "Name": "test_message",
            "Fields": [],  # Missing SIN and MIN
        },
        "invalid_sin": Message(
            Name="invalid",
            SIN=-1,  # Invalid negative SIN
            MIN=1,
            Fields=[],
        ),
        "invalid_json": "invalid json string",
        "invalid_field_type": {
            "Name": "invalid_field",
            "SIN": 16,
            "MIN": 1,
            "Fields": [{"Name": "field1", "Type": "invalid_type", "Value": "test"}],
        },
    }


@pytest.fixture
def valid_messages():
    """Create a collection of valid message scenarios."""
    return {
        "minimal": {
            "Name": "minimal",
            "SIN": 16,
            "MIN": 1,
            "Fields": [],
        },
        "with_fields": {
            "Name": "with_fields",
            "SIN": 16,
            "MIN": 1,
            "Fields": [{"Name": "field1", "Type": "string", "Value": "test"}],
        },
        "all_field_types": Message(
            Name="all_types",
            SIN=16,
            MIN=1,
            Fields=[
                Field(Name="string", Type=FieldType.STRING, Value="test"),
                Field(Name="int", Type=FieldType.SIGNED_INT, Value=42),
                Field(Name="uint", Type=FieldType.UNSIGNED_INT, Value=42),
                Field(Name="bool", Type=FieldType.BOOLEAN, Value=True),
                Field(Name="enum", Type=FieldType.ENUM, Value="OPTION_A"),
            ],
        ),
    }
