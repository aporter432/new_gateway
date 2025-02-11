"""Integration tests for OGx error flow functionality"""

import pytest

from protocols.ogx.encoding.json.decoder import decode_message
from protocols.ogx.encoding.json.encoder import encode_message
from protocols.ogx.validation.common.validation_exceptions import EncodingError, ValidationError
from protocols.ogx.validation.json.message_validator import OGxMessageValidator
from src.protocols.ogx.models.messages import OGxMessage


@pytest.fixture
def validator():
    """Create a message validator instance"""
    return OGxMessageValidator()


def test_error_propagation(validator):
    """Test error handling and propagation through the stack"""
    # Create an invalid message (missing required fields)
    invalid_message = {
        "Name": "test_message",
        # Missing SIN and MIN
        "Fields": [],
    }

    # Test validation error propagation
    with pytest.raises(ValidationError) as exc_info:
        validator.validate_message(invalid_message)
    assert exc_info.value.error_code == ValidationError.MISSING_REQUIRED_FIELD

    # Test encoding error propagation
    class InvalidMessage:
        """Test class for invalid message scenarios"""

        def to_dict(self):
            """Simulate a message that fails during serialization.

            Raises:
                ValueError: Always raises to simulate serialization failure.
            """
            raise ValueError("Invalid message")

    with pytest.raises(EncodingError):
        encode_message(InvalidMessage())

    # Test decoding error propagation
    with pytest.raises(EncodingError):
        decode_message("invalid json")


def test_validation_and_encoding_interaction(validator):
    """Test interaction between validation and encoding/decoding"""
    # Test that validation errors are caught before encoding
    invalid_message = OGxMessage(name="invalid", sin=-1, min=1, fields=[])  # Invalid negative SIN

    with pytest.raises(ValidationError):
        dict_message = invalid_message.to_dict()
        validator.validate_message(dict_message)

    # Test that decoded messages are always valid
    valid_message = {
        "Name": "valid",
        "SIN": 16,
        "MIN": 1,
        "Fields": [{"Name": "field1", "Type": "string", "Value": "test"}],
    }

    # Should not raise any errors
    validator.validate_message(valid_message)
    message_obj = OGxMessage.from_dict(valid_message)
    assert isinstance(message_obj, OGxMessage)
