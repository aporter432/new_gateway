"""Unit tests for array field validation according to OGWS-1.txt Table 3.

Tests focus on array field validation:
- No Value attribute allowed
- Optional Elements array
- Element structure validation
- Index validation (sequential, unique)
- Nested field validation
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


class TestArrayFieldValidation:
    """Test array field validation."""

    def test_array_field_basic_validation(self, field_validator, validation_context):
        """Test basic array field validation."""
        # Valid empty array
        field_data = {"Name": "test", "Type": "array"}
        result = field_validator.validate(field_data, validation_context)
        assert result.is_valid

        # Valid array with elements
        field_data = {
            "Name": "test",
            "Type": "array",
            "Elements": [
                {"Index": 0, "Fields": [{"Name": "item", "Type": "string", "Value": "test"}]}
            ],
        }
        result = field_validator.validate(field_data, validation_context)
        assert result.is_valid

        # Array with Value (invalid)
        field_data = {"Name": "test", "Type": "array", "Value": "test"}
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert "Invalid array field: Value attribute not allowed" in result.errors[0]

    def test_array_element_structure(self, field_validator, validation_context):
        """Test array element structure validation."""
        # Missing Index
        field_data = {
            "Name": "test",
            "Type": "array",
            "Elements": [{"Fields": [{"Name": "item", "Type": "string", "Value": "test"}]}],
        }
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert "Invalid array element at index 0: Missing required field Index" in result.errors[0]

        # Missing Fields
        field_data = {"Name": "test", "Type": "array", "Elements": [{"Index": 0}]}
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert "Invalid array element at index 0: Missing required field Fields" in result.errors[0]

        # Non-list Fields
        field_data = {
            "Name": "test",
            "Type": "array",
            "Elements": [{"Index": 0, "Fields": "not a list"}],
        }
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert "Invalid array element at index 0: Fields must be a list" in result.errors[0]

    def test_array_index_validation(self, field_validator, validation_context):
        """Test array element index validation."""
        # Non-sequential indices
        field_data = {
            "Name": "test",
            "Type": "array",
            "Elements": [
                {
                    "Index": 1,  # Should start at 0
                    "Fields": [{"Name": "item", "Type": "string", "Value": "test"}],
                }
            ],
        }
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert "Invalid array element at index 0: Index must be 0" in result.errors[0]

        # Duplicate indices
        field_data = {
            "Name": "test",
            "Type": "array",
            "Elements": [
                {"Index": 0, "Fields": [{"Name": "item", "Type": "string", "Value": "test1"}]},
                {"Index": 0, "Fields": [{"Name": "item", "Type": "string", "Value": "test2"}]},
            ],
        }
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert "Invalid array element at index 1: Index must be 1" in result.errors[0]

    def test_array_nested_field_validation(self, field_validator, validation_context):
        """Test validation of fields within array elements."""
        # Invalid field in element
        field_data = {
            "Name": "test",
            "Type": "array",
            "Elements": [
                {
                    "Index": 0,
                    "Fields": [
                        {
                            "Name": "item",
                            "Type": "unsignedint",
                            "Value": -1,  # Invalid negative value
                        }
                    ],
                }
            ],
        }
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert "Invalid unsignedint field: Value must be non-negative" in result.errors[0]

    def test_array_without_context(self, field_validator):
        """Test array validation without context."""
        # Array validation should work without context
        field_data = {
            "Name": "test",
            "Type": "array",
            "Elements": [{"Index": 0, "Fields": []}],
        }
        result = field_validator.validate(field_data, None)
        assert result.is_valid
