"""Unit tests for basic field type validation according to OGWS-1.txt Table 3.

Tests focus on basic field types:
- String fields
- Integer fields (signed/unsigned)
- Boolean fields
- Enum fields
- Data (base64) fields
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


class TestBasicFieldValidation:
    """Test basic field type validation."""

    def test_string_field_validation(self, field_validator, validation_context):
        """Test string field validation."""
        # Valid string
        field_data = {"Name": "test", "Type": "string", "Value": "test"}
        result = field_validator.validate(field_data, validation_context)
        assert result.is_valid

        # Invalid type (non-string)
        field_data = {"Name": "test", "Type": "string", "Value": 123}
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert "Invalid string field: Value must be a string" in result.errors[0]

        # Null value
        field_data = {"Name": "test", "Type": "string", "Value": None}
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert "Invalid string field: Missing required value" in result.errors[0]

    def test_unsigned_int_field_validation(self, field_validator, validation_context):
        """Test unsigned integer field validation."""
        # Valid positive int
        field_data = {"Name": "test", "Type": "unsignedint", "Value": 42}
        result = field_validator.validate(field_data, validation_context)
        assert result.is_valid

        # Invalid negative value
        field_data = {"Name": "test", "Type": "unsignedint", "Value": -1}
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert "Invalid unsignedint field: Value must be non-negative" in result.errors[0]

        # Invalid type
        field_data = {"Name": "test", "Type": "unsignedint", "Value": "not a number"}
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert "Invalid unsignedint field: Value must be an integer" in result.errors[0]

    def test_signed_int_field_validation(self, field_validator, validation_context):
        """Test signed integer field validation."""
        # Valid positive and negative
        for value in [42, -42]:
            field_data = {"Name": "test", "Type": "signedint", "Value": value}
            result = field_validator.validate(field_data, validation_context)
            assert result.is_valid

        # Invalid type
        field_data = {"Name": "test", "Type": "signedint", "Value": "not a number"}
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert "Invalid signedint field: Value must be an integer" in result.errors[0]

    def test_boolean_field_validation(self, field_validator, validation_context):
        """Test boolean field validation."""
        # Valid boolean values
        for value in [True, False, "true", "false", "True", "False", "1", "0"]:
            field_data = {"Name": "test", "Type": "boolean", "Value": value}
            result = field_validator.validate(field_data, validation_context)
            assert result.is_valid

        # Invalid value
        field_data = {"Name": "test", "Type": "boolean", "Value": "not a boolean"}
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert "Invalid boolean field: Value must be a boolean" in result.errors[0]

    def test_enum_field_validation(self, field_validator, validation_context):
        """Test enum field validation."""
        # Valid enum
        field_data = {"Name": "test", "Type": "enum", "Value": "VALID_ENUM"}
        result = field_validator.validate(field_data, validation_context)
        assert result.is_valid

        # Empty string
        field_data = {"Name": "test", "Type": "enum", "Value": ""}
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert "Invalid enum field: Value must be a non-empty string" in result.errors[0]

        # Invalid type
        field_data = {"Name": "test", "Type": "enum", "Value": 123}
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert "Invalid enum field: Value must be a non-empty string" in result.errors[0]

    def test_data_field_validation(self, field_validator, validation_context):
        """Test base64 data field validation."""
        # Valid base64
        field_data = {"Name": "test", "Type": "data", "Value": "SGVsbG8gV29ybGQ="}  # "Hello World"
        result = field_validator.validate(field_data, validation_context)
        assert result.is_valid

        # Valid empty string
        field_data = {"Name": "test", "Type": "data", "Value": ""}
        result = field_validator.validate(field_data, validation_context)
        assert result.is_valid

        # Invalid base64 padding
        field_data = {"Name": "test", "Type": "data", "Value": "SGVsbG8=a"}
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert "Invalid data field: Value must be a valid base64 encoded string" in result.errors[0]

        # Invalid type
        field_data = {"Name": "test", "Type": "data", "Value": 123}
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert "Invalid data field: Value must be a base64 encoded string" in result.errors[0]
