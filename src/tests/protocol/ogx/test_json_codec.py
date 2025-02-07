"""Tests for OGx JSON encoding/decoding"""

import json

import pytest

from protocols.ogx.encoding.json.json_codec import OGxJsonCodec
from src.protocols.ogx.constants import FieldType
from src.protocols.ogx.exceptions import EncodingError
from src.protocols.ogx.models.fields import Field
from src.protocols.ogx.models.messages import OGxMessage


class TestOGxJsonCodec:
    """Test suite for OGx JSON codec functionality"""

    @pytest.fixture
    def codec(self):
        """Create a JSON codec instance for testing"""
        return OGxJsonCodec()

    @pytest.fixture
    def sample_message(self):
        """Create a sample message for testing"""
        fields = [
            Field(name="field1", type=FieldType.STRING, value="test"),
            Field(name="field2", type=FieldType.UNSIGNED_INT, value=42),
        ]
        return OGxMessage(name="test_message", sin=16, min=1, fields=fields)

    def test_encode_valid_message(self, codec, sample_message):
        """Test encoding a valid message to JSON"""
        json_str = codec.encode(sample_message)

        # Verify it's valid JSON
        data = json.loads(json_str)
        assert data["Name"] == "test_message"
        assert data["SIN"] == 16
        assert data["MIN"] == 1
        assert len(data["Fields"]) == 2
        assert data["Fields"][0]["Name"] == "field1"
        assert data["Fields"][0]["Value"] == "test"
        assert data["Fields"][1]["Name"] == "field2"
        assert data["Fields"][1]["Value"] == 42

    def test_decode_valid_json(self, codec):
        """Test decoding valid JSON to a message"""
        json_data = {
            "Name": "test_message",
            "SIN": 16,
            "MIN": 1,
            "Fields": [{"Name": "field1", "Type": "string", "Value": "test"}],
        }

        # Test decoding from dict
        message = codec.decode(json_data)
        assert message.name == "test_message"
        assert message.sin == 16
        assert message.min == 1
        assert len(message.fields) == 1
        assert message.fields[0].name == "field1"
        assert message.fields[0].value == "test"

        # Test decoding from JSON string
        message = codec.decode(json.dumps(json_data))
        assert message.name == "test_message"
        assert message.sin == 16
        assert message.min == 1

    def test_encode_decode_roundtrip(self, codec, sample_message):
        """Test round-trip encoding and decoding"""
        json_str = codec.encode(sample_message)
        decoded_message = codec.decode(json_str)

        assert decoded_message.name == sample_message.name
        assert decoded_message.sin == sample_message.sin
        assert decoded_message.min == sample_message.min
        assert len(decoded_message.fields) == len(sample_message.fields)

        for orig_field, decoded_field in zip(sample_message.fields, decoded_message.fields):
            assert decoded_field.name == orig_field.name
            assert decoded_field.type == orig_field.type
            assert decoded_field.value == orig_field.value

    def test_decode_invalid_json(self, codec):
        """Test decoding invalid JSON"""
        # Invalid JSON string
        with pytest.raises(EncodingError):
            codec.decode("{invalid json")

        # Missing required fields
        with pytest.raises(EncodingError):
            codec.decode('{"Name": "test"}')

    def test_encode_invalid_message(self, codec):
        """Test encoding an invalid message"""

        class InvalidMessage:
            """Test class for invalid message scenarios"""

            def to_dict(self):
                """Return an invalid message dictionary"""
                raise ValueError("Invalid message")

        with pytest.raises(EncodingError):
            codec.encode(InvalidMessage())

    def test_decode_complex_message(self, codec):
        """Test decoding a complex message with nested elements"""
        json_data = {
            "Name": "complex_message",
            "SIN": 16,
            "MIN": 1,
            "Fields": [
                {
                    "Name": "array_field",
                    "Type": "array",
                    "Elements": [
                        {
                            "Index": 0,
                            "Fields": [{"Name": "sub_field", "Type": "string", "Value": "test"}],
                        }
                    ],
                }
            ],
        }

        message = codec.decode(json_data)
        assert message.name == "complex_message"
        assert len(message.fields) == 1
        assert message.fields[0].type == FieldType.ARRAY
        assert len(message.fields[0].elements) == 1
        assert message.fields[0].elements[0].index == 0
