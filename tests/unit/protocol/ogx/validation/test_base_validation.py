"""Unit tests for OGxBaseValidator edge cases.

Tests edge cases and error conditions for the OGxBaseValidator class implementation
according to OGx-1.txt Section 5 specifications.
"""

from typing import Any

import pytest

from Protexis_Command.api.config import NetworkType
from Protexis_Command.protocols.ogx.constants.ogx_field_types import FieldType
from Protexis_Command.protocols.ogx.constants.ogx_message_types import MessageType
from Protexis_Command.protocols.ogx.validation.ogx_validation_exceptions import ValidationError
from Protexis_Command.protocols.ogx.validation.validators.ogx_base_validator import OGxBaseValidator
from Protexis_Command.protocols.ogx.validation.validators.ogx_type_validator import (
    ValidationContext,
    ValidationResult,
)

# pylint: disable=protected-access
# Accessing protected members is expected in unit tests


class MockOGxBaseValidator(OGxBaseValidator):
    """Mock implementation of abstract OGxBaseValidator for testing."""

    def validate(self, data: Any, context: ValidationContext) -> ValidationResult:
        """Mock implementation of abstract validate method."""
        self.context = context
        return self._get_validation_result()


@pytest.fixture
def validator() -> MockOGxBaseValidator:
    """Fixture providing MockOGxBaseValidator instance."""
    return MockOGxBaseValidator()


@pytest.fixture
def context():
    """Provide test validation context."""
    return ValidationContext(network_type=NetworkType.OGX, direction=MessageType.FORWARD)


class TestOGxBaseValidatorEdgeCases:
    """Test edge cases for OGxBaseValidator implementation."""

    def test_validate_required_fields_empty_data(self, validator: MockOGxBaseValidator):
        """Test validation of required fields with empty data."""
        with pytest.raises(ValidationError) as exc:
            validator._validate_required_fields({}, {"required_field"}, "test")
        assert "Missing required test fields: required_field" in str(exc.value)

    def test_validate_required_fields_none_data(self, validator: MockOGxBaseValidator):
        """Test validation of required fields with None values."""
        data = {"required_field": None}
        # Should not raise - None is a valid value, just must be present
        validator._validate_required_fields(data, {"required_field"}, "test")

    def test_validate_required_fields_extra_fields(self, validator: MockOGxBaseValidator):
        """Test validation with extra unrequired fields."""
        data = {"required_field": "value", "extra_field": "extra"}
        # Should not raise - extra fields are allowed
        validator._validate_required_fields(data, {"required_field"}, "test")

    @pytest.mark.parametrize(
        "field_type,valid_value,invalid_value",
        [
            (FieldType.BOOLEAN, True, "INVALID_BOOL"),
            (FieldType.UNSIGNED_INT, 42, -1),
            (FieldType.SIGNED_INT, -42, "not_an_int"),
            (FieldType.STRING, "valid", b"bytes"),
            (FieldType.ARRAY, [], "not_a_list"),
            (FieldType.MESSAGE, {}, "not_a_dict"),
        ],
    )
    def test_validate_field_type_edge_cases(
        self,
        validator: MockOGxBaseValidator,
        field_type: FieldType,
        valid_value: Any,
        invalid_value: Any,
    ):
        """Test field type validation edge cases for each type."""
        # Valid value should not raise
        validator._validate_field_type(field_type, valid_value)

        # Invalid value should raise ValidationError
        with pytest.raises(ValidationError):
            validator._validate_field_type(field_type, invalid_value)

    def test_validate_dynamic_field_type_missing_attribute(self, validator: MockOGxBaseValidator):
        """Test dynamic field validation without type attribute."""
        with pytest.raises(ValidationError) as exc:
            validator._validate_field_type(FieldType.DYNAMIC, "value")
        assert "Type attribute required" in str(exc.value)

    def test_validate_dynamic_field_type_invalid_attribute(self, validator: MockOGxBaseValidator):
        """Test dynamic field validation with invalid type attribute."""
        with pytest.raises(ValidationError):
            validator._validate_field_type(FieldType.DYNAMIC, "value", "invalid_type")

    def test_validate_property_field_edge_cases(self, validator: MockOGxBaseValidator):
        """Test property field validation edge cases."""
        # Valid property field
        validator._validate_field_type(FieldType.PROPERTY, "42", "signedint")

        # Missing type attribute
        with pytest.raises(ValidationError):
            validator._validate_field_type(FieldType.PROPERTY, "value")

        # Invalid type attribute
        with pytest.raises(ValidationError):
            validator._validate_field_type(FieldType.PROPERTY, "value", "invalid_type")

        # Valid type but invalid value
        with pytest.raises(ValidationError):
            validator._validate_field_type(FieldType.PROPERTY, "not_a_number", "signedint")

    def test_string_number_conversion(self, validator: MockOGxBaseValidator):
        """Test edge cases for string-to-number conversion."""
        # String representations should work for numeric types
        validator._validate_field_type(FieldType.UNSIGNED_INT, "42")
        validator._validate_field_type(FieldType.SIGNED_INT, "-42")

        # Float strings should be converted properly
        validator._validate_field_type(FieldType.UNSIGNED_INT, "42.0")
        validator._validate_field_type(FieldType.SIGNED_INT, "-42.0")

        # Invalid number strings should fail
        with pytest.raises(ValidationError):
            validator._validate_field_type(FieldType.UNSIGNED_INT, "not_a_number")
        with pytest.raises(ValidationError):
            validator._validate_field_type(FieldType.SIGNED_INT, "invalid")

    def test_none_values(self, validator: MockOGxBaseValidator):
        """Test handling of None values for different field types."""
        # None should be valid for array and message types
        validator._validate_field_type(FieldType.ARRAY, None)
        validator._validate_field_type(FieldType.MESSAGE, None)

        # None should be invalid for other types
        for field_type in [
            FieldType.BOOLEAN,
            FieldType.UNSIGNED_INT,
            FieldType.SIGNED_INT,
            FieldType.STRING,
        ]:
            with pytest.raises(ValidationError):
                validator._validate_field_type(field_type, None)

    def test_error_accumulation(self, validator: MockOGxBaseValidator):
        """Test that errors accumulate properly."""
        validator._add_error("First error")
        validator._add_error("Second error")

        result = validator._get_validation_result()
        assert len(result.errors) == 2
        assert "First error" in result.errors
        assert "Second error" in result.errors
        assert not result.is_valid

    def test_validation_context_preservation(
        self, validator: MockOGxBaseValidator, context: ValidationContext
    ):
        """Test that validation context is preserved."""
        result = validator.validate({}, context)
        assert result.context == context

    def test_empty_validation_result(self, validator: MockOGxBaseValidator):
        """Test validation result with no errors."""
        result = validator._get_validation_result()
        assert result.is_valid
        assert not result.errors
        assert result.context is None

    def test_dynamic_field_type_resolution(self, validator: MockOGxBaseValidator):
        """Test dynamic field type resolution and validation."""
        # Test successful type resolution and validation
        validator._validate_field_type(FieldType.DYNAMIC, True, "boolean")
        validator._validate_field_type(FieldType.DYNAMIC, 42, "unsignedint")
        validator._validate_field_type(FieldType.DYNAMIC, "test", "string")

        # Test case sensitivity in type resolution
        validator._validate_field_type(FieldType.DYNAMIC, True, "BOOLEAN")
        validator._validate_field_type(FieldType.DYNAMIC, 42, "UNSIGNEDINT")

        # Test invalid resolved type validation
        with pytest.raises(ValidationError):
            validator._validate_field_type(FieldType.DYNAMIC, "not_a_number", "unsignedint")

        # Test invalid type resolution
        with pytest.raises(ValidationError):
            validator._validate_field_type(FieldType.DYNAMIC, "value", "nonexistent_type")

    def test_field_type_validation_edge_cases(self, validator: MockOGxBaseValidator):
        """Test specific edge cases for field type validation."""
        # Test boolean edge cases
        with pytest.raises(ValidationError):
            validator._validate_field_type(FieldType.BOOLEAN, 1)  # Integer that evaluates to True
        with pytest.raises(ValidationError):
            validator._validate_field_type(
                FieldType.BOOLEAN, "True"
            )  # String that evaluates to True

        # Test unsigned int edge cases
        validator._validate_field_type(FieldType.UNSIGNED_INT, 0)  # Zero is valid
        with pytest.raises(ValidationError):
            validator._validate_field_type(FieldType.UNSIGNED_INT, "not_a_number")

        # Test signed int edge cases
        validator._validate_field_type(FieldType.SIGNED_INT, "-0")  # String zero
        validator._validate_field_type(FieldType.SIGNED_INT, "0")  # String zero
        with pytest.raises(ValidationError):
            validator._validate_field_type(FieldType.SIGNED_INT, "not_a_number")

        # Test string edge cases
        with pytest.raises(ValidationError):
            validator._validate_field_type(FieldType.STRING, 123)  # Number
        with pytest.raises(ValidationError):
            validator._validate_field_type(FieldType.STRING, True)  # Boolean
        with pytest.raises(ValidationError):
            validator._validate_field_type(FieldType.STRING, b"bytes")  # Bytes

        # Test array edge cases
        validator._validate_field_type(FieldType.ARRAY, [])  # Empty list
        validator._validate_field_type(FieldType.ARRAY, None)  # None value
        with pytest.raises(ValidationError):
            validator._validate_field_type(FieldType.ARRAY, tuple())  # Tuple
        with pytest.raises(ValidationError):
            validator._validate_field_type(FieldType.ARRAY, set())  # Set

        # Test message edge cases
        validator._validate_field_type(FieldType.MESSAGE, {})  # Empty dict
        validator._validate_field_type(FieldType.MESSAGE, None)  # None value
        with pytest.raises(ValidationError):
            validator._validate_field_type(FieldType.MESSAGE, [])  # List
        with pytest.raises(ValidationError):
            validator._validate_field_type(FieldType.MESSAGE, "not_a_dict")  # String

    def test_dynamic_field_empty_type_attribute(self, validator: MockOGxBaseValidator):
        """Test dynamic field with empty type attribute."""
        with pytest.raises(ValidationError) as exc:
            validator._validate_field_type(FieldType.DYNAMIC, "value", "")
        assert "Type attribute required" in str(exc.value)

        with pytest.raises(ValidationError) as exc:
            validator._validate_field_type(FieldType.PROPERTY, "value", None)
        assert "Type attribute required" in str(exc.value)

    def test_dynamic_field_type_resolution_error(self, validator: MockOGxBaseValidator):
        """Test dynamic field type resolution with invalid type."""
        with pytest.raises(ValidationError):
            validator._validate_field_type(FieldType.DYNAMIC, "value", "invalid_type")

    def test_boolean_validation_error_paths(self, validator: MockOGxBaseValidator):
        """Test boolean validation error paths."""
        # Test various non-boolean values
        invalid_values = [1, 0, "True", "False", [], {}, None]
        for value in invalid_values:
            with pytest.raises(ValidationError):
                validator._validate_field_type(FieldType.BOOLEAN, value)

    def test_signed_int_validation_error_paths(self, validator: MockOGxBaseValidator):
        """Test signed int validation error paths."""
        # Test invalid signed int values
        invalid_values = ["abc", "12.34.56", [], {}, None, object()]
        for value in invalid_values:
            with pytest.raises(ValidationError):
                validator._validate_field_type(FieldType.SIGNED_INT, value)

        # Test valid edge cases
        valid_values = ["-0", "0", "-1.0", "1.0", -1, 0, 1]
        for value in valid_values:
            validator._validate_field_type(FieldType.SIGNED_INT, value)

    def test_string_validation_error_paths(self, validator: MockOGxBaseValidator):
        """Test string validation error paths."""
        # Test various non-string values
        invalid_values = [1, 1.0, True, [], {}, None, b"bytes"]
        for value in invalid_values:
            with pytest.raises(ValidationError):
                validator._validate_field_type(FieldType.STRING, value)

    def test_array_validation_error_paths(self, validator: MockOGxBaseValidator):
        """Test array validation error paths."""
        # Test various non-array values
        invalid_values = [1, "string", True, {}, set(), tuple(), frozenset(), (1, 2, 3), range(5)]
        for value in invalid_values:
            with pytest.raises(ValidationError):
                validator._validate_field_type(FieldType.ARRAY, value)

        # Test valid cases including None
        valid_values = [[], [1, 2, 3], None]
        for value in valid_values:
            validator._validate_field_type(FieldType.ARRAY, value)

    def test_message_validation_error_paths(self, validator: MockOGxBaseValidator):
        """Test message validation error paths."""
        # Test various non-dict values
        invalid_values = [1, "string", True, [], set(), tuple(), frozenset(), (1, 2, 3), range(5)]
        for value in invalid_values:
            with pytest.raises(ValidationError):
                validator._validate_field_type(FieldType.MESSAGE, value)

        # Test valid cases including None
        valid_values = [{}, {"key": "value"}, None]
        for value in valid_values:
            validator._validate_field_type(FieldType.MESSAGE, value)

    def test_field_type_validation_with_type_error(self, validator: MockOGxBaseValidator):
        """Test field type validation when TypeError is raised."""

        # Create a custom object that raises TypeError on comparison
        class BadComparison:
            """Test class that raises TypeError when compared."""

            def __lt__(self, other):
                raise TypeError("Cannot compare")

        with pytest.raises(ValidationError):
            validator._validate_field_type(FieldType.UNSIGNED_INT, BadComparison())

    def test_field_type_validation_with_value_error(self, validator: MockOGxBaseValidator):
        """Test field type validation when ValueError is raised."""
        # Test with a value that will cause int() to raise ValueError
        with pytest.raises(ValidationError):
            validator._validate_field_type(
                FieldType.UNSIGNED_INT, "123.45.67"
            )  # Malformed number string

    def test_field_validation_with_recursive_error(self, validator: MockOGxBaseValidator):
        """Test field validation with recursive error propagation."""
        # Test dynamic field with invalid nested type validation
        with pytest.raises(ValidationError):
            validator._validate_field_type(
                FieldType.DYNAMIC,
                "invalid",
                "unsignedint",  # Valid type attribute but invalid value
            )
