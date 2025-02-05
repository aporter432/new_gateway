"""Additional tests for MTWS protocol JSON codec.

This module contains additional tests to improve coverage of the JSON codec
implementation defined in N206 section 2.4.2.
"""

import pytest

from protocols.mtws.constants import PROTOCOL_VERSION
from protocols.mtws.encoding.json_codec import JSONCodec
from protocols.mtws.exceptions import MTWSEncodingError
from protocols.mtws.models.messages import CommonMessage, CommonMessageField


def test_encode_edge_cases():
    """Test JSON encoding edge cases."""
    codec = JSONCodec()

    # Test encoding message with no fields
    message = CommonMessage(name="test", sin=1, min_value=1, version=PROTOCOL_VERSION)
    encoded = codec.encode(message)
    assert isinstance(encoded, str)
    assert "test" in encoded
    assert "Fields" not in encoded

    # Test encoding message with empty fields list
    message = CommonMessage(name="test", sin=1, min_value=1, version=PROTOCOL_VERSION, fields=[])
    encoded = codec.encode(message)
    assert isinstance(encoded, str)
    assert "Fields" not in encoded  # Empty fields list should be omitted


def test_decode_edge_cases():
    """Test JSON decoding edge cases."""
    codec = JSONCodec()

    # Test decoding non-dict JSON
    with pytest.raises(MTWSEncodingError) as exc_info:
        codec.decode("[1, 2, 3]")  # Array instead of object
    assert exc_info.value.error_code == MTWSEncodingError.INVALID_JSON_FORMAT

    # Test decoding empty object
    with pytest.raises(MTWSEncodingError) as exc_info:
        codec.decode("{}")
    assert exc_info.value.error_code == MTWSEncodingError.INVALID_JSON_FORMAT

    # Test decoding minimal valid message
    minimal_json = """
    {
        "Name": "test",
        "SIN": 1,
        "MIN": 1,
        "Version": "2.0.6",
        "IsForward": false
    }
    """
    message = codec.decode(minimal_json)
    assert message.name == "test"
    assert message.sin == 1
    assert message.min_value == 1
    assert message.version == "2.0.6"
    assert not message.is_forward


def test_encode_decode_roundtrip():
    """Test encoding and decoding roundtrip with various field types."""
    codec = JSONCodec()

    # Create message with different field types
    original = CommonMessage(
        name="test",
        sin=1,
        min_value=1,
        version=PROTOCOL_VERSION,
        is_forward=True,
        sequence=1,
        fields=[
            CommonMessageField(name="string", value="test"),
            CommonMessageField(name="integer", value="123"),
            CommonMessageField(name="float", value="123.45"),
            CommonMessageField(name="boolean", value="true"),
        ],
    )

    # Encode and decode
    encoded = codec.encode(original)
    decoded = codec.decode(encoded)

    # Verify all fields preserved
    assert decoded.name == original.name
    assert decoded.sin == original.sin
    assert decoded.min_value == original.min_value
    assert decoded.version == original.version
    assert decoded.is_forward == original.is_forward
    assert decoded.sequence == original.sequence
    assert len(decoded.fields) == len(original.fields)

    # Verify field values preserved
    field_values = {f.name: f.value for f in decoded.fields}
    assert field_values["string"] == "test"
    assert field_values["integer"] == "123"
    assert field_values["float"] == "123.45"
    assert field_values["boolean"] == "true"
