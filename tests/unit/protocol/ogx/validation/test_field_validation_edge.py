"""Unit tests for field validation edge cases and error handling.

Tests focus on edge cases and error handling:
- Required field validation
- Invalid field types
- Error propagation
- Null/empty values
- Complex error scenarios
"""

import pytest

from protocols.ogx.constants import MessageType, NetworkType
from protocols.ogx.validation.common.types import ValidationContext
from protocols.ogx.validation.message.field_validator import OGxFieldValidator


@pytest.fixture
def field_validator() -> OGxFieldValidator:
    """Provide field validator instance."""
    return OGxFieldValidator()


@pytest.fixture
def context():
    """Provide test validation context."""
    return ValidationContext(network_type=NetworkType.OGX, direction=MessageType.FORWARD)


class TestFieldValidationEdgeCases:
    """Test field validation edge cases and error handling."""

    def test_required_field_validation(self, field_validator, context):
        """Test validation of required field properties."""
        # Missing Name
        field_data = {"Type": "string", "Value": "test"}
        result = field_validator.validate(field_data, context)
        assert not result.is_valid
        assert "Missing required field fields: Name" in result.errors[0]

        # Missing Type
        field_data = {"Name": "test", "Value": "test"}
        result = field_validator.validate(field_data, context)
        assert not result.is_valid
        assert "Missing required field fields: Type" in result.errors[0]

        # None input
        result = field_validator.validate(None, context)
        assert not result.is_valid
        assert (
            "Required field data missing - Name and Type properties are required"
            in result.errors[0]
        )

    def test_invalid_field_type(self, field_validator, context):
        """Test validation with invalid field type."""
        field_data = {"Name": "test", "Type": "invalid_type", "Value": "test"}
        result = field_validator.validate(field_data, context)
        assert not result.is_valid
        assert "Invalid field type: invalid_type" in result.errors[0]

    def test_error_propagation(self, field_validator, context):
        """Test error propagation in nested structures."""
        # Nested message validation error
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
                        "Type": "dynamic",
                        "TypeAttribute": "invalid",  # This will cause error
                        "Value": "test",
                    }
                ],
            },
        }
        result = field_validator.validate(field_data, context)
        assert not result.is_valid
        assert (
            "In nested message: Field validation error: Invalid dynamic field: TypeAttribute invalid not allowed"
            in result.errors[0]
        )

        # Nested array validation error
        field_data = {
            "Name": "test",
            "Type": "array",
            "Elements": [
                {
                    "Index": 0,
                    "Fields": [
                        {
                            "Name": "nested",
                            "Type": "dynamic",
                            "TypeAttribute": "invalid",  # This will cause error
                            "Value": "test",
                        }
                    ],
                }
            ],
        }
        result = field_validator.validate(field_data, context)
        assert not result.is_valid
        assert "Invalid dynamic field: TypeAttribute invalid not allowed" in result.errors[0]

    def test_concurrent_validation_errors(self, field_validator, context):
        """Test handling of multiple validation errors."""
        field_data = {
            "Name": "test",
            "Type": "message",
            "Message": {
                "Name": "inner",
                "SIN": 16,
                "MIN": 1,
                "Fields": [
                    {"Name": "field1", "Type": "string", "Value": 123},  # Invalid string
                    {"Name": "field2", "Type": "unsignedint", "Value": -1},  # Invalid unsigned int
                    {"Name": "field3", "Type": "boolean", "Value": "invalid"},  # Invalid boolean
                ],
            },
        }
        result = field_validator.validate(field_data, context)
        assert not result.is_valid
        assert len([err for err in result.errors if "Invalid" in err]) >= 3

    def test_deep_nested_validation(self, field_validator, context):
        """Test validation of deeply nested structures."""
        field_data = {
            "Name": "outer",
            "Type": "message",
            "Message": {
                "Name": "level1",
                "SIN": 16,
                "MIN": 1,
                "Fields": [
                    {
                        "Name": "middle",
                        "Type": "array",
                        "Elements": [
                            {
                                "Index": 0,
                                "Fields": [
                                    {
                                        "Name": "inner",
                                        "Type": "dynamic",
                                        "TypeAttribute": "string",
                                        "Value": 123,  # Invalid string value
                                    }
                                ],
                            }
                        ],
                    }
                ],
            },
        }
        result = field_validator.validate(field_data, context)
        assert not result.is_valid
        assert (
            "In nested message: Field validation error: In array element 0: In array element 0: Invalid string field: Value must be a string"
            in str(result.errors)
        )
