"""Integration tests for message field validation according to OGWS-1.txt Section 5."""

import pytest

from protocols.ogx.constants.message_types import MessageType
from protocols.ogx.validation.common.validation_exceptions import ValidationError
from protocols.ogx.validation.common.types import ValidationContext
from protocols.ogx.validation.message.field_validator import OGxFieldValidator


@pytest.fixture
def field_validator() -> OGxFieldValidator:
    """Provide configured field validator."""
    return OGxFieldValidator()


@pytest.fixture
def validation_context() -> ValidationContext:
    """Provide validation context for tests."""
    return ValidationContext(network_type="OGx", direction=MessageType.FORWARD)


class TestMessageValidation:
    """Test message field validation according to OGWS-1.txt."""

    def test_message_field_validation(self, field_validator, validation_context):
        """Test validation of message field constraints."""
        # Valid nested message
        field_data = {
            "Name": "msg",
            "Type": "message",
            "Message": {"Name": "nested", "SIN": 16, "MIN": 1, "Fields": []},
        }
        result = field_validator.validate(field_data, validation_context)
        assert result.is_valid

        # Message with Value (invalid)
        with pytest.raises(ValidationError, match=".*must not have Value attribute.*"):
            field_data = {"Name": "invalid", "Type": "message", "Value": "test"}
            field_validator.validate(field_data, validation_context)

        # Invalid nested message (missing required fields)
        with pytest.raises(ValidationError, match=".*missing required fields.*"):
            field_data = {"Name": "msg", "Type": "message", "Message": {"Name": "invalid"}}
            field_validator.validate(field_data, validation_context)

    def test_message_required_fields(self, field_validator, validation_context):
        """Test validation of required message fields."""
        # Missing SIN
        with pytest.raises(ValidationError, match=".*missing required fields: SIN.*"):
            field_data = {
                "Name": "msg",
                "Type": "message",
                "Message": {"Name": "nested", "MIN": 1, "Fields": []},
            }
            field_validator.validate(field_data, validation_context)

        # Missing MIN
        with pytest.raises(ValidationError, match=".*missing required fields: MIN.*"):
            field_data = {
                "Name": "msg",
                "Type": "message",
                "Message": {"Name": "nested", "SIN": 16, "Fields": []},
            }
            field_validator.validate(field_data, validation_context)

        # Missing Fields
        with pytest.raises(ValidationError, match=".*missing required fields: Fields.*"):
            field_data = {
                "Name": "msg",
                "Type": "message",
                "Message": {"Name": "nested", "SIN": 16, "MIN": 1},
            }
            field_validator.validate(field_data, validation_context)

    def test_message_field_types(self, field_validator, validation_context):
        """Test validation of message field types."""
        # Invalid SIN type
        with pytest.raises(ValidationError, match=".*SIN must be.*"):
            field_data = {
                "Name": "msg",
                "Type": "message",
                "Message": {"Name": "nested", "SIN": "16", "MIN": 1, "Fields": []},
            }
            field_validator.validate(field_data, validation_context)

        # Invalid MIN type
        with pytest.raises(ValidationError, match=".*MIN must be.*"):
            field_data = {
                "Name": "msg",
                "Type": "message",
                "Message": {"Name": "nested", "SIN": 16, "MIN": "1", "Fields": []},
            }
            field_validator.validate(field_data, validation_context)

        # Invalid Fields type
        with pytest.raises(ValidationError, match=".*Fields must be.*"):
            field_data = {
                "Name": "msg",
                "Type": "message",
                "Message": {"Name": "nested", "SIN": 16, "MIN": 1, "Fields": "invalid"},
            }
            field_validator.validate(field_data, validation_context)
