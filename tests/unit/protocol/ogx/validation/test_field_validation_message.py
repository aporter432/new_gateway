"""Unit tests for message field validation according to OGWS-1.txt Table 3.

Tests focus on message field validation:
- No Value attribute allowed
- Message attribute required
- Message content validation
- Required fields (SIN, MIN, Fields)
- Context requirements
"""

import pytest

from protocols.ogx.constants.message_types import MessageType
from protocols.ogx.validation.common.types import ValidationContext
from protocols.ogx.validation.message.field_validator import OGxFieldValidator


@pytest.fixture
def field_validator() -> OGxFieldValidator:
    """Provide field validator instance."""
    return OGxFieldValidator()


@pytest.fixture
def validation_context() -> ValidationContext:
    """Provide validation context."""
    return ValidationContext(network_type="OGx", direction=MessageType.FORWARD)


class TestMessageFieldValidation:
    """Test message field validation."""

    def test_message_field_basic_validation(self, field_validator, validation_context):
        """Test basic message field validation."""
        # Valid message field
        field_data = {
            "Name": "test",
            "Type": "message",
            "Message": {"Name": "inner", "SIN": 16, "MIN": 1, "Fields": []},
        }
        result = field_validator.validate(field_data, validation_context)
        assert result.is_valid

        # Message with Value (invalid)
        field_data = {"Name": "test", "Type": "message", "Value": "test"}
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert "Invalid message field: Value attribute not allowed" in result.errors[0]

        # Missing Message attribute
        field_data = {"Name": "test", "Type": "message"}
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert "Invalid message field: Missing required field Message" in result.errors[0]

    def test_message_content_validation(self, field_validator, validation_context):
        """Test message content validation."""
        # Empty dictionary
        field_data = {"Name": "test", "Type": "message", "Message": {}}
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert "Invalid message field: Message must be a non-empty dictionary" in result.errors[0]

        # Non-dictionary Message
        field_data = {"Name": "test", "Type": "message", "Message": "not a dict"}
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert "Invalid message field: Message must be a non-empty dictionary" in result.errors[0]

    def test_required_message_fields(self, field_validator, validation_context):
        """Test required message field validation."""
        # Missing SIN
        field_data = {
            "Name": "test",
            "Type": "message",
            "Message": {"Name": "inner", "MIN": 1, "Fields": []},
        }
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert "Invalid message field: Missing required fields SIN" in result.errors[0]

        # Missing MIN
        field_data = {
            "Name": "test",
            "Type": "message",
            "Message": {"Name": "inner", "SIN": 16, "Fields": []},
        }
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert "Invalid message field: Missing required fields MIN" in result.errors[0]

        # Missing Fields
        field_data = {
            "Name": "test",
            "Type": "message",
            "Message": {"Name": "inner", "SIN": 16, "MIN": 1},
        }
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert "Invalid message field: Missing required fields Fields" in result.errors[0]

    def test_nested_field_validation(self, field_validator, validation_context):
        """Test validation of fields within message."""
        # Invalid field in message
        field_data = {
            "Name": "test",
            "Type": "message",
            "Message": {
                "Name": "inner",
                "SIN": 16,
                "MIN": 1,
                "Fields": [
                    {
                        "Name": "nested",
                        "Type": "unsignedint",
                        "Value": -1,  # Invalid negative value
                    }
                ],
            },
        }
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert (
            "In nested message: Field validation error: Invalid unsignedint field: Value must be non-negative"
            in result.errors[0]
        )

    def test_message_without_context(self, field_validator):
        """Test message validation without context."""
        # Message validation requires context
        field_data = {
            "Name": "test",
            "Type": "message",
            "Message": {"Name": "inner", "SIN": 16, "MIN": 1, "Fields": []},
        }
        result = field_validator.validate(field_data, None)
        assert not result.is_valid
        assert "Invalid message field: Validation context required" in result.errors[0]
