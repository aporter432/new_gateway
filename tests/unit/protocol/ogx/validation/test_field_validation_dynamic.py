"""Unit tests for dynamic field validation according to OGWS-1.txt Table 3.

Tests focus on dynamic field validation:
- TypeAttribute required
- TypeAttribute must be valid basic type
- Value must match TypeAttribute type
- Property fields (same rules as dynamic)
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


class TestDynamicFieldValidation:
    """Test dynamic field validation."""

    def test_dynamic_field_basic_validation(self, field_validator, validation_context):
        """Test basic dynamic field validation."""
        # Valid dynamic field
        field_data = {
            "Name": "test",
            "Type": "dynamic",
            "TypeAttribute": "string",
            "Value": "test",
        }
        result = field_validator.validate(field_data, validation_context)
        assert result.is_valid

        # Missing TypeAttribute
        field_data = {"Name": "test", "Type": "dynamic", "Value": "test"}
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert "Invalid dynamic field: Missing required field TypeAttribute" in result.errors[0]

        # Empty TypeAttribute
        field_data = {
            "Name": "test",
            "Type": "dynamic",
            "TypeAttribute": "",
            "Value": "test",
        }
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert "Invalid dynamic field: Missing required field TypeAttribute" in result.errors[0]

    def test_dynamic_field_type_validation(self, field_validator, validation_context):
        """Test dynamic field type validation."""
        # Invalid TypeAttribute
        field_data = {
            "Name": "test",
            "Type": "dynamic",
            "TypeAttribute": "invalid_type",
            "Value": "test",
        }
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert "Invalid dynamic field: TypeAttribute invalid_type not allowed" in result.errors[0]

        # Value doesn't match TypeAttribute type
        field_data = {
            "Name": "test",
            "Type": "dynamic",
            "TypeAttribute": "unsignedint",
            "Value": "not a number",
        }
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert "Invalid unsignedint field: Value must be an integer" in result.errors[0]

    def test_dynamic_field_null_value(self, field_validator, validation_context):
        """Test dynamic field null value validation."""
        # Null value
        field_data = {
            "Name": "test",
            "Type": "dynamic",
            "TypeAttribute": "string",
            "Value": None,
        }
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert "Invalid string field: Value must be a string" in result.errors[0]

    def test_property_field_validation(self, field_validator, validation_context):
        """Test property field validation (same rules as dynamic)."""
        # Valid property field
        field_data = {
            "Name": "test",
            "Type": "property",
            "TypeAttribute": "string",
            "Value": "test",
        }
        result = field_validator.validate(field_data, validation_context)
        assert result.is_valid

        # Missing TypeAttribute
        field_data = {"Name": "test", "Type": "property", "Value": "test"}
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert "Invalid property field: Missing required field TypeAttribute" in result.errors[0]

        # Invalid TypeAttribute
        field_data = {
            "Name": "test",
            "Type": "property",
            "TypeAttribute": "invalid_type",
            "Value": "test",
        }
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert "Invalid property field: TypeAttribute invalid_type not allowed" in result.errors[0]
