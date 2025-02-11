"""Integration tests for OGx forward message flow functionality"""

import pytest

from protocols.ogx.constants import FieldType
from protocols.ogx.encoding.json.decoder import decode_message
from protocols.ogx.encoding.json.encoder import encode_message
from protocols.ogx.validation.json.message_validator import OGxMessageValidator
from src.protocols.ogx.models.fields import ArrayField, Element, Field
from src.protocols.ogx.models.messages import OGxMessage


@pytest.fixture
def validator():
    """Create a message validator instance"""
    return OGxMessageValidator()


def test_complete_message_lifecycle(validator):
    """Test complete message lifecycle: create -> validate -> encode -> decode -> validate"""
    # Create a complex message with various field types
    fields = [
        Field(name="string_field", type=FieldType.STRING, value="test"),
        Field(name="int_field", type=FieldType.SIGNED_INT, value=-42),
        ArrayField(
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

    original_message = OGxMessage(name="test_message", sin=16, min=1, fields=fields)

    # Step 1: Initial validation
    dict_message = original_message.to_dict()
    validator.validate_message(dict_message)

    # Step 2: Encode to JSON
    json_str = encode_message(original_message)

    # Step 3: Decode from JSON
    decoded_message = decode_message(json_str)

    # Step 4: Validate decoded message
    dict_message = decoded_message.to_dict()
    validator.validate_message(dict_message)

    # Step 5: Verify content equality
    assert decoded_message.name == original_message.name
    assert decoded_message.sin == original_message.sin
    assert decoded_message.min == original_message.min
    assert len(decoded_message.fields) == len(original_message.fields)


def test_field_type_conversion():
    """Test field type conversion and preservation through encode/decode cycle"""
    # Create fields with different types and edge case values
    fields = [
        Field(name="max_uint", type=FieldType.UNSIGNED_INT, value=2**32 - 1),
        Field(name="min_int", type=FieldType.SIGNED_INT, value=-(2**31)),
        Field(name="bool_field", type=FieldType.BOOLEAN, value=True),
        Field(name="empty_string", type=FieldType.STRING, value=""),
        Field(name="unicode_string", type=FieldType.STRING, value="Hello 世界 🌍"),
        Field(name="enum_field", type=FieldType.ENUM, value="OPTION_A"),
    ]

    message = OGxMessage(name="type_test", sin=16, min=1, fields=fields)

    # Encode and decode
    json_str = encode_message(message)
    decoded = decode_message(json_str)

    # Verify type and value preservation
    for original, decoded_field in zip(message.fields, decoded.fields):
        assert decoded_field.type == original.type
        assert decoded_field.value == original.value
        assert isinstance(decoded_field.value, type(original.value))
