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

    def test_array_field_validation_with_missing_context(self, field_validator: OGxFieldValidator):
        """Test array field validation when context is missing."""
        field_data = {
            "Name": "test_array",
            "Type": "array",
            "Elements": [{"Index": 0, "Fields": []}],
        }

        # Clear the context
        field_validator.context = None

        result = field_validator.validate(field_data, None)
        assert not result.is_valid
        assert any("context is required" in error for error in result.errors)

    def test_array_field_with_invalid_elements(
        self, field_validator: OGxFieldValidator, validation_context: ValidationContext
    ):
        """Test array field validation with invalid elements."""
        field_data = {
            "Name": "test_array",
            "Type": "array",
            "Elements": [{"Invalid": "element"}],  # Missing required Index and Fields
        }

        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert len(result.errors) > 0

    def test_array_field_with_both_value_and_elements(
        self, field_validator: OGxFieldValidator, validation_context: ValidationContext
    ):
        """Test array field validation when both Value and Elements are present."""
        field_data = {
            "Name": "test_array",
            "Type": "array",
            "Value": "should not be here",
            "Elements": [{"Index": 0, "Fields": []}],
        }

        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert any("must not have Value attribute" in error for error in result.errors)

    def test_array_field_validation_error_propagation(
        self, field_validator: OGxFieldValidator, validation_context: ValidationContext
    ):
        """Test array field validation error propagation."""
        field_data = {
            "Name": "test_array",
            "Type": "array",
            "Elements": [
                {
                    "Index": 0,
                    "Fields": [
                        {
                            "Name": "test_field",
                            "Type": "unsignedint",
                            "Value": -1,
                        }  # Invalid value for unsigned int
                    ],
                }
            ],
        }

        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert len(result.errors) > 0

    def test_message_field_validation_error_paths(
        self, field_validator: OGxFieldValidator, validation_context: ValidationContext
    ):
        """Test message field validation error paths."""
        # Test with Value attribute (should fail)
        field_data = {
            "Name": "test_message",
            "Type": "message",
            "Value": "should not be here",
            "Message": {},
        }
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert any("must not have Value attribute" in error for error in result.errors)

        # Test with missing Message attribute
        field_data = {
            "Name": "test_message",
            "Type": "message",
        }
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert any("must have Message attribute" in error for error in result.errors)

    def test_message_field_validation_error_propagation(
        self, field_validator: OGxFieldValidator, validation_context: ValidationContext
    ):
        """Test message field validation error propagation."""
        field_data = {
            "Name": "test_message",
            "Type": "message",
            "Message": {
                "Name": "test_submessage",
                "Fields": [
                    {
                        "Name": "test_field",
                        "Type": "boolean",
                        "Value": "not_a_boolean",
                    }  # Invalid boolean value
                ],
            },
        }

        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert len(result.errors) > 0

    def test_dynamic_field_validation_paths(
        self, field_validator: OGxFieldValidator, validation_context: ValidationContext
    ):
        """Test dynamic field validation paths."""
        # Test dynamic field with valid type attribute and value
        field_data = {
            "Name": "test_dynamic",
            "Type": "dynamic",
            "TypeAttribute": "string",
            "Value": "test",
        }
        result = field_validator.validate(field_data, validation_context)
        assert result.is_valid

        # Test dynamic field with missing type attribute
        field_data = {"Name": "test_dynamic", "Type": "dynamic", "Value": "test"}
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert any("TypeAttribute" in error for error in result.errors)

        # Test dynamic field with invalid type attribute
        field_data = {
            "Name": "test_dynamic",
            "Type": "dynamic",
            "TypeAttribute": "invalid_type",
            "Value": "test",
        }
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert any("Invalid TypeAttribute" in error for error in result.errors)

        # Test dynamic field with valid type attribute but invalid value
        field_data = {
            "Name": "test_dynamic",
            "Type": "dynamic",
            "TypeAttribute": "boolean",
            "Value": "not a boolean",
        }
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert any("Invalid value" in error for error in result.errors)

    def test_field_validation_with_invalid_type_attribute(
        self, field_validator: OGxFieldValidator, validation_context: ValidationContext
    ):
        """Test field validation with invalid type attribute."""
        field_data = {
            "Name": "test_field",
            "Type": "dynamic",
            "TypeAttribute": "invalid_type",
            "Value": "test",
        }

        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert any("Invalid TypeAttribute" in error for error in result.errors)

    def test_array_field_with_missing_elements(
        self, field_validator: OGxFieldValidator, validation_context: ValidationContext
    ):
        """Test array field validation with missing Elements attribute."""
        field_data = {
            "Name": "test_array",
            "Type": "array",
        }

        result = field_validator.validate(field_data, validation_context)
        assert result.is_valid  # Elements is optional

    def test_message_field_with_missing_message(
        self, field_validator: OGxFieldValidator, validation_context: ValidationContext
    ):
        """Test message field validation with missing Message attribute."""
        field_data = {
            "Name": "test_message",
            "Type": "message",
        }

        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert any("must have Message attribute" in error for error in result.errors)

    def test_field_validation_with_unknown_type(
        self, field_validator: OGxFieldValidator, validation_context: ValidationContext
    ):
        """Test field validation with unknown field type."""
        field_data = {
            "Name": "test_field",
            "Type": "unknown",
            "Value": "test",
        }

        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert any("Invalid field type" in error for error in result.errors)

    def test_array_field_validation_error_handling(
        self, field_validator: OGxFieldValidator, validation_context: ValidationContext
    ):
        """Test array field validation error handling."""
        field_data = {
            "Name": "test_array",
            "Type": "array",
            "Elements": [
                {
                    "Index": 0,
                    "Fields": [
                        {
                            "Name": "test_field",
                            "Type": "unsignedint",
                            "Value": "not_a_number",  # Will cause ValueError
                        }
                    ],
                }
            ],
        }
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert any("Invalid value for type" in error for error in result.errors)

    def test_message_field_validation_error_handling(
        self, field_validator: OGxFieldValidator, validation_context: ValidationContext
    ):
        """Test message field validation error handling."""
        field_data = {
            "Name": "test_message",
            "Type": "message",
            "Message": {
                "Name": "test_submessage",
                "SIN": 16,
                "MIN": 1,
                "Fields": [
                    {
                        "Name": "test_field",
                        "Type": "unsignedint",
                        "Value": "not_a_number",  # Will cause ValueError
                    }
                ],
            },
        }
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert any("Invalid value for type" in error for error in result.errors)
