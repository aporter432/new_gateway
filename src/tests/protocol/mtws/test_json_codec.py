"""Tests for MTWS protocol JSON codec implementation.

This module contains tests that verify the JSON encoding and decoding functionality
follows the specifications defined in N206 section 2.4.2.
"""

import json

import pytest

from protocols.mtws.constants import (
    MAX_MESSAGE_SIZE,
    PROTOCOL_VERSION,
)
from protocols.mtws.encoding.json_codec import JSONCodec
from protocols.mtws.exceptions import MTWSEncodingError, MTWSFieldError
from protocols.mtws.models.messages import (
    CommonMessage,
    CommonMessageElement,
    CommonMessageElementList,
    CommonMessageField,
)


@pytest.fixture(name="json_codec")
def codec_fixture():
    """Create a JSON codec instance for testing."""
    return JSONCodec()


class TestMTWSJsonCodec:
    """Test suite for MTWS JSON codec implementation."""

    def test_encode_basic_message(self, json_codec):
        """Test encoding of basic MTWS message to JSON."""
        message = CommonMessage(
            name="getProperties",
            sin=16,
            min_value=8,
            is_forward=False,
            version=PROTOCOL_VERSION,
            fields=[
                CommonMessageField(
                    name="list",
                    elements=CommonMessageElementList(
                        elements=[
                            CommonMessageElement(
                                index=0,
                                fields=[
                                    CommonMessageField(name="sin", value="16"),
                                    CommonMessageField(name="pinList", value="AQID"),
                                ],
                            )
                        ]
                    ),
                )
            ],
        )

        json_str = json_codec.encode(message)
        assert isinstance(json_str, str)
        assert "getProperties" in json_str
        assert "Version" in json_str
        assert "IsForward" in json_str

    def test_decode_basic_message(self, json_codec):
        """Test decoding of a JSON string to MTWS message."""
        json_str = """
        {
            "Name": "getProperties",
            "SIN": 16,
            "MIN": 8,
            "Version": "2.0.6",
            "IsForward": false,
            "Fields": [
                {
                    "Name": "list",
                    "Elements": [
                        {
                            "Index": 0,
                            "Fields": [
                                {"Name": "sin", "Value": "16"},
                                {"Name": "pinList", "Value": "AQID"}
                            ]
                        }
                    ]
                }
            ]
        }
        """

        message = json_codec.decode(json_str)
        assert isinstance(message, CommonMessage)
        assert message.name == "getProperties"
        assert message.sin == 16
        assert message.min_value == 8
        assert message.version == PROTOCOL_VERSION
        assert not message.is_forward
        assert len(message.fields) == 1
        assert message.fields[0].name == "list"
        assert isinstance(message.fields[0].elements, CommonMessageElementList)
        assert len(message.fields[0].elements.elements) == 1
        assert message.fields[0].elements.elements[0].index == 0

    def test_encode_nested_structure(self, json_codec):
        """Test encoding of nested message structure."""
        message = CommonMessage(
            name="complexTest",
            sin=16,
            min_value=1,
            is_forward=False,
            version=PROTOCOL_VERSION,
            fields=[
                CommonMessageField(
                    name="outer",
                    elements=CommonMessageElementList(
                        elements=[
                            CommonMessageElement(
                                index=0,
                                fields=[
                                    CommonMessageField(name="inner", value="test"),
                                ],
                            )
                        ]
                    ),
                )
            ],
        )

        json_str = json_codec.encode(message)
        assert isinstance(json_str, str)
        assert "complexTest" in json_str
        assert "outer" in json_str
        assert "inner" in json_str

    def test_invalid_json_handling(self, json_codec):
        """Test handling of invalid JSON data according to N206 section 2.4.2."""
        # Test invalid JSON string
        with pytest.raises(MTWSEncodingError) as exc_info:
            json_codec.decode("invalid json")
        assert exc_info.value.error_code == MTWSEncodingError.INVALID_JSON_FORMAT

        # Test missing required fields
        with pytest.raises(MTWSEncodingError) as exc_info:
            json_codec.decode('{"Name": "test"}')  # Missing SIN, MIN, etc.
        assert exc_info.value.error_code == MTWSEncodingError.INVALID_JSON_FORMAT

        # Test invalid field structure
        with pytest.raises(MTWSEncodingError) as exc_info:
            json_codec.decode(
                json.dumps(
                    {
                        "Name": "test",
                        "SIN": 16,
                        "MIN": 1,
                        "Version": PROTOCOL_VERSION,
                        "IsForward": False,
                        "Fields": [{"Name": "field1"}],  # Missing value/message/elements
                    }
                )
            )
        assert exc_info.value.error_code == MTWSEncodingError.DECODE_FAILED

    def test_encode_size_limits(self, json_codec):
        """Test encoding size limits according to N206 section 2.4.3."""
        # Test message approaching size limit
        large_message = CommonMessage(
            name="test",
            sin=16,
            min_value=1,
            version=PROTOCOL_VERSION,
            is_forward=False,
            fields=[
                CommonMessageField(
                    name="field1",
                    value="x" * (MAX_MESSAGE_SIZE // 2),  # Large but valid value
                )
            ],
        )
        encoded = json_codec.encode(large_message)
        assert len(encoded) <= MAX_MESSAGE_SIZE

        # Test message exceeding size limit
        with pytest.raises(MTWSFieldError) as exc_info:
            CommonMessage(
                name="test",
                sin=16,
                min_value=1,
                version=PROTOCOL_VERSION,
                is_forward=False,
                fields=[
                    CommonMessageField(
                        name="field1",
                        value="x" * MAX_MESSAGE_SIZE,  # Value too large
                    )
                ],
            )
        assert exc_info.value.error_code == MTWSFieldError.INVALID_LENGTH
