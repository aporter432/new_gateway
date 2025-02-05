"""Tests for MTWS protocol integration.

This module contains integration tests that verify the interaction between
different components of the MTWS protocol implementation.
"""

import pytest

from protocols.mtws.constants import PROTOCOL_VERSION
from protocols.mtws.encoding.json_codec import JSONCodec
from protocols.mtws.exceptions import MTWSElementError, MTWSEncodingError, MTWSFieldError
from protocols.mtws.models.messages import (
    CommonMessage,
    CommonMessageElement,
    CommonMessageElementList,
    CommonMessageField,
)
from protocols.mtws.validation.validation import MTWSProtocolValidator


@pytest.fixture(name="validator")
def validator_fixture():
    """Create a protocol validator instance for testing."""
    return MTWSProtocolValidator()


@pytest.fixture(name="codec")
def codec_fixture():
    """Create a JSON codec instance for testing."""
    return JSONCodec()


class TestMTWSIntegration:
    """Test suite for MTWS protocol integration."""

    def test_encode_decode_validation(self, validator, codec):
        """Test encoding, decoding and validation workflow."""
        # Create a valid message
        message = CommonMessage(
            name="test",
            sin=16,
            min_value=1,
            version=PROTOCOL_VERSION,
            is_forward=False,
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

        # Encode message
        encoded = codec.encode(message)
        assert isinstance(encoded, str)

        # Validate encoded message
        validator.validate_message_size(encoded)

        # Decode message
        decoded = codec.decode(encoded)
        assert isinstance(decoded, CommonMessage)
        assert decoded.name == message.name
        assert decoded.sin == message.sin
        assert decoded.min_value == message.min_value
        assert decoded.version == message.version
        assert not decoded.is_forward

    def test_invalid_message_handling(self, codec):
        """Test handling of invalid messages in the workflow."""
        # Create message with invalid field
        message = CommonMessage(
            name="test",
            sin=16,
            min_value=1,
            version=PROTOCOL_VERSION,
            is_forward=False,
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

        # Encode message
        encoded = codec.encode(message)

        # Corrupt the encoded message to make it invalid JSON
        corrupted = encoded[:-1]  # Remove closing brace to make invalid JSON

        # Attempt to decode corrupted message
        with pytest.raises(MTWSEncodingError) as exc_info:
            codec.decode(corrupted)
        assert exc_info.value.error_code == MTWSEncodingError.INVALID_JSON_FORMAT

    def test_field_validation_workflow(self):
        """Test field validation in the workflow."""
        # Create message with invalid field name
        with pytest.raises(MTWSFieldError) as exc_info:
            CommonMessage(
                name="test",
                sin=16,
                min_value=1,
                version=PROTOCOL_VERSION,
                is_forward=False,
                fields=[CommonMessageField(name="", value="test")],
            )
        assert exc_info.value.error_code == MTWSFieldError.INVALID_NAME

        # Create message with invalid field value
        with pytest.raises(MTWSFieldError) as exc_info:
            CommonMessage(
                name="test",
                sin=16,
                min_value=1,
                version=PROTOCOL_VERSION,
                is_forward=False,
                fields=[CommonMessageField(name="test")],  # Missing value
            )
        assert exc_info.value.error_code == MTWSFieldError.MISSING_VALUE

    def test_element_validation_workflow(self):
        """Test element validation in the workflow."""
        # Create message with invalid element index
        with pytest.raises(MTWSElementError) as exc_info:
            CommonMessage(
                name="test",
                sin=16,
                min_value=1,
                version=PROTOCOL_VERSION,
                is_forward=False,
                fields=[
                    CommonMessageField(
                        name="list",
                        elements=CommonMessageElementList(
                            elements=[
                                CommonMessageElement(
                                    index=-1,  # Invalid index
                                    fields=[CommonMessageField(name="test", value="test")],
                                )
                            ]
                        ),
                    )
                ],
            )
        assert exc_info.value.error_code == MTWSElementError.NEGATIVE_INDEX

    def test_size_validation_workflow(self):
        """Test size validation in the workflow."""
        # Create message with field value too large
        with pytest.raises(MTWSFieldError) as exc_info:
            CommonMessage(
                name="test",
                sin=16,
                min_value=1,
                version=PROTOCOL_VERSION,
                is_forward=False,
                fields=[
                    CommonMessageField(
                        name="test",
                        value="x" * 1025,  # Value too large
                    )
                ],
            )
        assert exc_info.value.error_code == MTWSFieldError.INVALID_LENGTH
