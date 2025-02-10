"""Unit tests for field validation according to OGWS-1.txt Section 5.1 Table 3.

Tests focus on basic field validation rules:
- Required properties (Name, Type)
- Value attribute requirements for basic types
- Type validation
- Dynamic/Property field validation
"""

from typing import Any, Dict

import pytest

from protocols.ogx.constants.message_types import MessageType
from protocols.ogx.validation.message.field_validator import OGxFieldValidator
from protocols.ogx.validation.common.types import ValidationContext


@pytest.fixture
def field_validator() -> OGxFieldValidator:
    """Provide field validator instance."""
    return OGxFieldValidator()


@pytest.fixture
def validation_context() -> ValidationContext:
    """Provide validation context."""
    return ValidationContext(network_type="OGx", direction=MessageType.FORWARD)


@pytest.fixture
def valid_field() -> Dict[str, Any]:
    """Provide valid field data for testing."""
    return {"Name": "test_field", "Type": "string", "Value": "test_value"}


class TestFieldValidator:
    """Test field validator implementation."""

    def test_validates_required_properties(
        self, field_validator: OGxFieldValidator, validation_context: ValidationContext
    ):
        """Test validation of required field properties."""
        # Missing required Name
        field_data = {"Type": "string", "Value": "test"}
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert "Name" in result.errors[0]

        # Missing required Type
        field_data = {"Name": "test", "Value": "test"}
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert "Type" in result.errors[0]

    def test_validates_field_type(
        self, field_validator: OGxFieldValidator, validation_context: ValidationContext
    ):
        """Test validation of field type."""
        # Invalid field type
        field_data = {"Name": "test", "Type": "invalid_type", "Value": "test"}
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert "Invalid field type" in result.errors[0]

    def test_validates_type_attribute(
        self, field_validator: OGxFieldValidator, validation_context: ValidationContext
    ):
        """Test validation of dynamic/property field type attributes."""
        # Dynamic field without type attribute
        field_data = {"Name": "test", "Type": "dynamic", "Value": "test"}
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert "TypeAttribute" in result.errors[0]

        # Dynamic field with invalid type attribute
        field_data = {
            "Name": "test",
            "Type": "dynamic",
            "TypeAttribute": "invalid",
            "Value": "test",
        }
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert "Invalid TypeAttribute" in result.errors[0]

        # Dynamic field with valid type attribute
        field_data = {
            "Name": "test",
            "Type": "dynamic",
            "TypeAttribute": "string",
            "Value": "test",
        }
        result = field_validator.validate(field_data, validation_context)
        assert result.is_valid

    def test_validates_field_values(
        self, field_validator: OGxFieldValidator, validation_context: ValidationContext
    ):
        """Test validation of field values against their types."""
        # Test unsigned int validation
        field_data = {"Name": "test", "Type": "unsignedint", "Value": -1}
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert "Invalid value for type FieldType.UNSIGNED_INT" in result.errors[0]

        # Test boolean validation
        field_data = {"Name": "test", "Type": "boolean", "Value": "not-a-bool"}
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert "Invalid value for type FieldType.BOOLEAN" in result.errors[0]

        # Test string validation
        field_data = {"Name": "test", "Type": "string", "Value": 123}
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert "Invalid value for type FieldType.STRING" in result.errors[0]

    def test_validates_value_requirements(
        self, field_validator: OGxFieldValidator, validation_context: ValidationContext
    ):
        """Test validation of Value attribute requirements."""
        # Basic type missing Value
        field_data = {"Name": "test", "Type": "string"}
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert "Value" in result.errors[0]

        # Array type with Value (should fail)
        field_data = {"Name": "test", "Type": "array", "Value": "test"}
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert "Array fields must not have Value attribute" in result.errors[0]

        # Message type with Value (should fail)
        field_data = {"Name": "test", "Type": "message", "Value": "test"}
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert "Message fields must not have Value attribute" in result.errors[0]
