"""Shared fixtures for integration tests"""

import pytest

from protocols.ogx.constants import FieldType
from protocols.ogx.models.fields import Element, Field, Message
from protocols.ogx.validation.message.message_validator import OGxMessageValidator


@pytest.fixture
def validator():
    """Create a message validator instance.

    This fixture provides a configured OGxMessageValidator instance
    that can be used across tests for message validation.
    """
    return OGxMessageValidator()


@pytest.fixture
def simple_message():
    """Create a simple OGx message with basic fields.

    This fixture provides a basic message structure that can be used
    as a starting point for tests requiring a valid message.
    """
    fields = [
        Field(name="string_field", type=FieldType.STRING, value="test"),
        Field(name="int_field", type=FieldType.SIGNED_INT, value=42),
    ]
    return Message(name="test_message", sin=16, min=1, fields=fields)


@pytest.fixture
def complex_message():
    """Create a complex OGx message with nested structures.

    This fixture provides a message with nested arrays and multiple field types,
    useful for testing complex message handling scenarios.
    """
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
    """Create a list of fields with edge case values.

    This fixture provides fields testing boundary conditions and special cases,
    useful for validation and encoding tests.
    """
    return [
        Field(name="max_uint", type=FieldType.UNSIGNED_INT, value=2**32 - 1),
        Field(name="min_int", type=FieldType.SIGNED_INT, value=-(2**31)),
        Field(name="bool_field", type=FieldType.BOOLEAN, value=True),
        Field(name="empty_string", type=FieldType.STRING, value=""),
        Field(name="unicode_string", type=FieldType.STRING, value="Hello 世界 🌍"),
        Field(name="enum_field", type=FieldType.ENUM, value="OPTION_A"),
    ]


@pytest.fixture
def nested_message():
    """Create a deeply nested message structure.

    This fixture provides a message with multiple levels of nesting,
    useful for testing complex validation and transformation scenarios.
    """
    nested_fields = [
        Field(
            name="level1",
            type=FieldType.ARRAY,
            elements=[
                Element(
                    index=0,
                    fields=[
                        Field(name="field1", type=FieldType.STRING, value="test"),
                        Field(
                            name="level2",
                            type=FieldType.ARRAY,
                            elements=[
                                Element(
                                    index=0,
                                    fields=[
                                        Field(name="field2", type=FieldType.BOOLEAN, value=True),
                                        Field(
                                            name="level3",
                                            type=FieldType.ARRAY,
                                            elements=[
                                                Element(
                                                    index=0,
                                                    fields=[
                                                        Field(
                                                            name="field3",
                                                            type=FieldType.UNSIGNED_INT,
                                                            value=42,
                                                        )
                                                    ],
                                                )
                                            ],
                                        ),
                                    ],
                                )
                            ],
                        ),
                    ],
                )
            ],
        )
    ]
    return Message(name="nested_test", sin=16, min=1, fields=nested_fields)


@pytest.fixture
def invalid_messages():
    """Create a collection of invalid message scenarios.

    This fixture provides various invalid message cases,
    useful for testing error handling and validation.
    """
    return {
        "missing_required": {
            "Name": "test_message",
            "Fields": [],  # Missing SIN and MIN
        },
        "invalid_sin": Message(
            name="invalid",
            sin=-1,  # Invalid negative SIN
            min=1,
            fields=[],
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
    """Create a collection of valid message scenarios.

    This fixture provides various valid message cases,
    useful for testing positive scenarios and edge cases.
    """
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
            name="all_types",
            sin=16,
            min=1,
            fields=[
                Field(name="string", type=FieldType.STRING, value="test"),
                Field(name="int", type=FieldType.SIGNED_INT, value=42),
                Field(name="uint", type=FieldType.UNSIGNED_INT, value=42),
                Field(name="bool", type=FieldType.BOOLEAN, value=True),
                Field(name="enum", type=FieldType.ENUM, value="OPTION_A"),
            ],
        ),
    }
