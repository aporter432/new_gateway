"""Integration tests for array element validation according to OGWS-1.txt Section 5."""

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


class TestElementValidation:
    """Test array element validation according to OGWS-1.txt."""

    def test_array_field_validation(self, field_validator, validation_context):
        """Test validation of array field constraints."""
        # Valid array with elements
        field_data = {
            "Name": "array",
            "Type": "array",
            "Elements": [
                {"Index": 0, "Fields": [{"Name": "item", "Type": "string", "Value": "test"}]}
            ],
        }
        result = field_validator.validate(field_data, validation_context)
        assert result.is_valid

        # Array with Value (invalid)
        with pytest.raises(ValidationError, match=".*must not have Value attribute.*"):
            field_data = {"Name": "invalid", "Type": "array", "Value": "test"}
            field_validator.validate(field_data, validation_context)

        # Empty Elements array
        field_data = {"Name": "array", "Type": "array", "Elements": []}
        result = field_validator.validate(field_data, validation_context)
        assert result.is_valid

    def test_array_element_index_validation(self, field_validator, validation_context):
        """Test validation of array element indices."""
        # Missing Index
        with pytest.raises(ValidationError, match=".*requires Index.*"):
            field_data = {
                "Name": "array",
                "Type": "array",
                "Elements": [{"Fields": [{"Name": "item", "Type": "string", "Value": "test"}]}],
            }
            field_validator.validate(field_data, validation_context)

        # Invalid Index type
        with pytest.raises(ValidationError, match=".*Index must be.*"):
            field_data = {
                "Name": "array",
                "Type": "array",
                "Elements": [
                    {"Index": "0", "Fields": [{"Name": "item", "Type": "string", "Value": "test"}]}
                ],
            }
            field_validator.validate(field_data, validation_context)

        # Negative Index
        with pytest.raises(ValidationError, match=".*Index must be.*"):
            field_data = {
                "Name": "array",
                "Type": "array",
                "Elements": [
                    {"Index": -1, "Fields": [{"Name": "item", "Type": "string", "Value": "test"}]}
                ],
            }
            field_validator.validate(field_data, validation_context)

    def test_array_element_fields_validation(self, field_validator, validation_context):
        """Test validation of array element fields."""
        # Missing Fields
        with pytest.raises(ValidationError, match=".*requires Fields.*"):
            field_data = {
                "Name": "array",
                "Type": "array",
                "Elements": [{"Index": 0}],
            }
            field_validator.validate(field_data, validation_context)

        # Empty Fields
        field_data = {
            "Name": "array",
            "Type": "array",
            "Elements": [{"Index": 0, "Fields": []}],
        }
        result = field_validator.validate(field_data, validation_context)
        assert result.is_valid

        # Invalid Fields type
        with pytest.raises(ValidationError, match=".*Fields must be.*"):
            field_data = {
                "Name": "array",
                "Type": "array",
                "Elements": [{"Index": 0, "Fields": "invalid"}],
            }
            field_validator.validate(field_data, validation_context)
