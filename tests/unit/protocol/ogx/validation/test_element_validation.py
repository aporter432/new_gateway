"""Unit tests for OGxElementValidator.

Tests validation of elements according to OGWS-1.txt requirements and
implementation standards.
"""

from unittest.mock import Mock

import pytest

from src.protocols.ogx.validation.common.types import ValidationContext
from src.protocols.ogx.validation.message.element_validator import OGxElementValidator


class TestOGxElementValidator:
    """Test cases for OGxElementValidator."""

    @pytest.fixture
    def validator(self):
        """Create a fresh validator instance for each test."""
        return OGxElementValidator()

    @pytest.fixture
    def context(self):
        """Create a mock validation context for tests."""
        mock_context = Mock(spec=ValidationContext)
        return mock_context

    @pytest.fixture
    def valid_element(self):
        """Create a valid element fixture."""
        return {"Index": 0, "Fields": []}  # Empty fields array is valid for element validation

    @pytest.fixture
    def valid_element_array(self, valid_element):
        """Create a valid array of elements fixture."""
        return [valid_element, {"Index": 1, "Fields": []}]

    def test_validate_valid_element(self, validator, context, valid_element):
        """Test validation of a valid single element."""
        result = validator.validate(valid_element, context)
        assert result.is_valid
        assert not result.errors

    def test_validate_valid_element_array(self, validator, context, valid_element_array):
        """Test validation of a valid array of elements."""
        result = validator.validate(valid_element_array, context)
        assert result.is_valid
        assert not result.errors

    def test_validate_invalid_data_type(self, validator, context):
        """Test validation with invalid data type (neither dict nor list)."""
        result = validator.validate("invalid", context)
        assert not result.is_valid
        assert "Invalid element data type" in result.errors[0]

    def test_validate_missing_index(self, validator, context, valid_element):
        """Test validation of element missing Index property."""
        del valid_element["Index"]
        result = validator.validate(valid_element, context)
        assert not result.is_valid
        assert any("Index" in error for error in result.errors)

    def test_validate_missing_fields(self, validator, context, valid_element):
        """Test validation of element missing Fields property."""
        del valid_element["Fields"]
        result = validator.validate(valid_element, context)
        assert not result.is_valid
        assert any("Fields" in error for error in result.errors)

    def test_validate_non_array_fields(self, validator, context, valid_element):
        """Test validation when Fields is not an array."""
        valid_element["Fields"] = "not an array"
        result = validator.validate(valid_element, context)
        assert not result.is_valid
        assert any("must be an array" in error for error in result.errors)

    def test_validate_empty_fields_array(self, validator, context, valid_element):
        """Test validation with empty Fields array."""
        valid_element["Fields"] = []
        result = validator.validate(valid_element, context)
        assert result.is_valid  # Empty arrays are valid according to spec
        assert not result.errors

    def test_validate_array_with_invalid_element(self, validator, context, valid_element_array):
        """Test validation of array containing an invalid element."""
        valid_element_array.append({"invalid": "element"})
        result = validator.validate(valid_element_array, context)
        assert not result.is_valid
        assert any("Index" in error for error in result.errors)

    def test_validate_non_array_input_to_validate_array(self, validator, context):
        """Test validate_array with non-array input."""
        result = validator.validate_array("not an array", context)
        assert not result.is_valid
        assert any("must be an array" in error for error in result.errors)

    def test_validate_empty_array(self, validator, context):
        """Test validation of empty array."""
        result = validator.validate([], context)
        assert result.is_valid  # Empty arrays are valid according to spec
        assert not result.errors
