"""Integration tests for field type validation according to OGWS-1.txt Section 5 and Table 3."""

import pytest

from protocols.ogx.constants.message_types import MessageType
from protocols.ogx.validation.common.types import ValidationContext
from protocols.ogx.validation.common.validation_exceptions import ValidationError
from protocols.ogx.validation.message.field_validator import OGxFieldValidator


@pytest.fixture
def field_validator() -> OGxFieldValidator:
    """Provide configured field validator."""
    return OGxFieldValidator()


@pytest.fixture
def validation_context() -> ValidationContext:
    """Provide validation context for tests."""
    return ValidationContext(network_type="OGx", direction=MessageType.FORWARD)


class TestFieldTypeValidation:
    """Test field type validation against OGWS-1.txt Table 3."""

    def test_string_validation(self, field_validator, validation_context):
        """Test validation of string fields."""
        # Valid string
        field_data = {"Name": "test", "Type": "string", "Value": "test value"}
        result = field_validator.validate(field_data, validation_context)
        assert result.is_valid

        # None value
        with pytest.raises(ValidationError, match=".*requires a non-null value.*"):
            field_data = {"Name": "test", "Type": "string", "Value": None}
            field_validator.validate(field_data, validation_context)

        # Wrong type
        with pytest.raises(ValidationError, match=".*requires a string value.*"):
            field_data = {"Name": "test", "Type": "string", "Value": 123}
            field_validator.validate(field_data, validation_context)

    def test_unsigned_int_validation(self, field_validator, validation_context):
        """Test validation of unsigned integer fields."""
        # Valid unsigned int
        field_data = {"Name": "count", "Type": "unsignedint", "Value": 42}
        result = field_validator.validate(field_data, validation_context)
        assert result.is_valid

        # Zero is valid
        field_data = {"Name": "count", "Type": "unsignedint", "Value": 0}
        result = field_validator.validate(field_data, validation_context)
        assert result.is_valid

        # Negative value
        with pytest.raises(ValidationError, match=".*requires a non-negative integer value.*"):
            field_data = {"Name": "count", "Type": "unsignedint", "Value": -1}
            field_validator.validate(field_data, validation_context)

        # String value
        with pytest.raises(ValidationError, match=".*requires a valid integer value.*"):
            field_data = {"Name": "count", "Type": "unsignedint", "Value": "42"}
            field_validator.validate(field_data, validation_context)

    def test_signed_int_validation(self, field_validator, validation_context):
        """Test validation of signed integer fields."""
        # Valid positive int
        field_data = {"Name": "temp", "Type": "signedint", "Value": 42}
        result = field_validator.validate(field_data, validation_context)
        assert result.is_valid

        # Valid negative int
        field_data = {"Name": "temp", "Type": "signedint", "Value": -42}
        result = field_validator.validate(field_data, validation_context)
        assert result.is_valid

        # Zero is valid
        field_data = {"Name": "temp", "Type": "signedint", "Value": 0}
        result = field_validator.validate(field_data, validation_context)
        assert result.is_valid

        # String value
        with pytest.raises(ValidationError, match=".*requires a valid integer value.*"):
            field_data = {"Name": "temp", "Type": "signedint", "Value": "42"}
            field_validator.validate(field_data, validation_context)

    def test_boolean_validation(self, field_validator, validation_context):
        """Test validation of boolean fields."""
        # Valid boolean values
        for value in [True, False]:
            field_data = {"Name": "flag", "Type": "boolean", "Value": value}
            result = field_validator.validate(field_data, validation_context)
            assert result.is_valid

        # String representations
        for value in ["true", "false", "True", "False", "1", "0"]:
            field_data = {"Name": "flag", "Type": "boolean", "Value": value}
            result = field_validator.validate(field_data, validation_context)
            assert result.is_valid

        # Invalid values
        for value in ["yes", "no", 1, 0, None, "invalid"]:
            with pytest.raises(ValidationError, match=".*requires a valid boolean value.*"):
                field_data = {"Name": "flag", "Type": "boolean", "Value": value}
                field_validator.validate(field_data, validation_context)

    def test_enum_validation(self, field_validator, validation_context):
        """Test validation of enum fields."""
        # Valid enum string
        field_data = {"Name": "status", "Type": "enum", "Value": "ACTIVE"}
        result = field_validator.validate(field_data, validation_context)
        assert result.is_valid

        # Empty string
        with pytest.raises(ValidationError, match=".*requires a non-empty string value.*"):
            field_data = {"Name": "status", "Type": "enum", "Value": ""}
            field_validator.validate(field_data, validation_context)

        # Non-string value
        with pytest.raises(ValidationError, match=".*requires a non-empty string value.*"):
            field_data = {"Name": "status", "Type": "enum", "Value": 123}
            field_validator.validate(field_data, validation_context)

    def test_data_validation(self, field_validator, validation_context):
        """Test validation of base64 data fields."""
        # Valid base64 string
        field_data = {"Name": "data", "Type": "data", "Value": "SGVsbG8gV29ybGQ="}  # "Hello World"
        result = field_validator.validate(field_data, validation_context)
        assert result.is_valid

        # Invalid base64 padding
        with pytest.raises(ValidationError, match=".*requires a valid base64.*"):
            field_data = {"Name": "data", "Type": "data", "Value": "SGVsbG8gV29ybGQ"}
            field_validator.validate(field_data, validation_context)

        # Non-string value
        with pytest.raises(ValidationError, match=".*requires a base64 encoded string.*"):
            field_data = {"Name": "data", "Type": "data", "Value": 123}
            field_validator.validate(field_data, validation_context)

    def test_dynamic_field_validation(self, field_validator, validation_context):
        """Test validation of dynamic fields."""
        # Valid dynamic field using string type
        field_data = {
            "Name": "dynamic",
            "Type": "dynamic",
            "TypeAttribute": "string",
            "Value": "test",
        }
        result = field_validator.validate(field_data, validation_context)
        assert result.is_valid

        # Missing TypeAttribute
        with pytest.raises(ValidationError, match=".*requires TypeAttribute.*"):
            field_data = {"Name": "dynamic", "Type": "dynamic", "Value": "test"}
            field_validator.validate(field_data, validation_context)

        # Invalid TypeAttribute
        with pytest.raises(ValidationError, match=".*Invalid TypeAttribute.*"):
            field_data = {
                "Name": "dynamic",
                "Type": "dynamic",
                "TypeAttribute": "invalid",
                "Value": "test",
            }
            field_validator.validate(field_data, validation_context)

        # Value doesn't match TypeAttribute
        with pytest.raises(ValidationError, match=".*requires a valid integer value.*"):
            field_data = {
                "Name": "dynamic",
                "Type": "dynamic",
                "TypeAttribute": "unsignedint",
                "Value": "not a number",
            }
            field_validator.validate(field_data, validation_context)
