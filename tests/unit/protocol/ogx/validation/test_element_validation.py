"""Unit tests for element validation according to OGx-1.txt.

Tests focus on array element validation:
- Element structure validation
- Field validation within elements
- Error propagation
"""

import pytest
from protocols.ogx.constants.message_types import MessageType
from protocols.ogx.validation.common.types import ValidationContext
from protocols.ogx.validation.message.element_validator import OGxElementValidator


@pytest.fixture
def validator() -> OGxElementValidator:
    """Provide element validator instance."""
    return OGxElementValidator()


@pytest.fixture
def context() -> ValidationContext:
    """Provide validation context."""
    return ValidationContext(network_type="OGX", direction=MessageType.FORWARD)


class TestOGxElementValidator:
    """Test element validation."""

    def test_validate_valid_element(
        self, validator: OGxElementValidator, context: ValidationContext
    ):
        """Test validation of valid element."""
        element = {
            "Index": 0,
            "Fields": [{"Name": "test_field", "Type": "string", "Value": "test"}],
        }
        validator.context = context
        result = validator.validate(element, context)
        assert result.is_valid

    def test_validate_valid_element_array(
        self, validator: OGxElementValidator, context: ValidationContext
    ):
        """Test validation of array of valid elements."""
        elements = [
            {
                "Index": 0,
                "Fields": [{"Name": "test_field", "Type": "string", "Value": "test"}],
            },
            {
                "Index": 1,
                "Fields": [{"Name": "test_field", "Type": "string", "Value": "test"}],
            },
        ]
        validator.context = context
        result = validator.validate_array(elements, context)
        assert result.is_valid

    def test_validate_invalid_data_type(
        self, validator: OGxElementValidator, context: ValidationContext
    ):
        """Test validation with invalid data type."""
        element = "not a dictionary"
        validator.context = context
        result = validator.validate(element, context)
        assert not result.is_valid
        assert "Invalid element data type" in result.errors[0]

    def test_validate_missing_index(
        self, validator: OGxElementValidator, context: ValidationContext
    ):
        """Test validation with missing Index."""
        element = {"Fields": [{"Name": "test_field", "Type": "string", "Value": "test"}]}
        validator.context = context
        result = validator.validate(element, context)
        assert not result.is_valid
        assert "Missing required element fields: Index" in result.errors[0]

    def test_validate_missing_fields(
        self, validator: OGxElementValidator, context: ValidationContext
    ):
        """Test validation with missing Fields."""
        element = {"Index": 0}
        validator.context = context
        result = validator.validate(element, context)
        assert not result.is_valid
        assert "Missing required element fields: Fields" in result.errors[0]

    def test_validate_non_array_fields(
        self, validator: OGxElementValidator, context: ValidationContext
    ):
        """Test validation with non-array Fields."""
        element = {"Index": 0, "Fields": "not an array"}
        validator.context = context
        result = validator.validate(element, context)
        assert not result.is_valid
        assert "Element Fields must be an array" in result.errors[0]

    def test_validate_empty_fields_array(
        self, validator: OGxElementValidator, context: ValidationContext
    ):
        """Test validation with empty Fields array."""
        element = {"Index": 0, "Fields": []}
        validator.context = context
        result = validator.validate(element, context)
        assert result.is_valid

    def test_validate_array_with_invalid_element(
        self, validator: OGxElementValidator, context: ValidationContext
    ):
        """Test validation of array with invalid element."""
        elements = [
            {
                "Index": 0,
                "Fields": [{"Name": "test_field", "Type": "string", "Value": "test"}],
            },
            {"Index": 1},  # Invalid element missing Fields
        ]
        validator.context = context
        result = validator.validate_array(elements, context)
        assert not result.is_valid
        assert "Missing required element fields: Fields" in result.errors[0]

    def test_validate_non_array_input_to_validate_array(
        self, validator: OGxElementValidator, context: ValidationContext
    ):
        """Test validation_array with non-array input."""
        elements = "not an array"
        validator.context = context
        result = validator.validate_array(elements, context)
        assert not result.is_valid
        assert "Elements must be an array" in result.errors[0]

    def test_validate_empty_array(self, validator: OGxElementValidator, context: ValidationContext):
        """Test validation of empty array."""
        elements = []
        validator.context = context
        result = validator.validate_array(elements, context)
        assert result.is_valid

    def test_validate_element_with_invalid_field(
        self, validator: OGxElementValidator, context: ValidationContext
    ):
        """Test validation of element with invalid field."""
        element = {
            "Index": 0,
            "Fields": [
                {
                    "Name": "test_field",
                    "Type": "unsignedint",
                    "Value": -1,  # Invalid value for unsigned int
                }
            ],
        }
        validator.context = context  # Set context before validation
        result = validator.validate(element, context)
        assert not result.is_valid
        assert "Invalid unsignedint field: Value must be non-negative" in result.errors[0]

    def test_validate_element_with_field_validation_error(
        self, validator: OGxElementValidator, context: ValidationContext
    ):
        """Test validation when field validation raises an error."""
        element = {
            "Index": 0,
            "Fields": [
                {
                    "Name": "test_field",
                    "Type": "unsignedint",
                    "Value": "not_a_number",  # Will cause ValueError in field validation
                }
            ],
        }
        validator.context = context
        result = validator.validate(element, context)
        assert not result.is_valid
        assert "Invalid unsignedint field: Value must be an integer" in result.errors[0]

    def test_validate_element_with_no_context(self, validator: OGxElementValidator):
        """Test validation without context."""
        element = {
            "Index": 0,
            "Fields": [{"Name": "test_field", "Type": "string", "Value": "test"}],
        }
        result = validator.validate(element, None)
        assert result.is_valid
