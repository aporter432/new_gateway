"""Unit tests for OGxMessageValidator.

Tests validation of messages according to OGWS-1.txt Section 5 requirements and
implementation standards.
"""

from unittest.mock import Mock

import pytest

from src.protocols.ogx.validation.common.types import ValidationContext
from src.protocols.ogx.validation.message.message_validator import OGxMessageValidator


class TestOGxMessageValidator:
    """Test cases for OGxMessageValidator."""

    @pytest.fixture
    def validator(self):
        """Create a fresh validator instance for each test."""
        return OGxMessageValidator()

    @pytest.fixture
    def context(self):
        """Create a mock validation context for tests."""
        mock_context = Mock(spec=ValidationContext)
        return mock_context

    @pytest.fixture
    def valid_message(self):
        """Create a valid message fixture."""
        return {
            "Name": "test_message",
            "SIN": 16,
            "MIN": 1,
            "Fields": [],  # Empty fields array is valid for message validation
        }

    def test_validate_valid_message(self, validator, context, valid_message):
        """Test validation of a valid message."""
        result = validator.validate(valid_message, context)
        assert result.is_valid
        assert not result.errors

    def test_validate_missing_name(self, validator, context, valid_message):
        """Test validation of message missing Name property."""
        del valid_message["Name"]
        result = validator.validate(valid_message, context)
        assert not result.is_valid
        assert any("Name" in error for error in result.errors)

    def test_validate_missing_sin(self, validator, context, valid_message):
        """Test validation of message missing SIN property."""
        del valid_message["SIN"]
        result = validator.validate(valid_message, context)
        assert not result.is_valid
        assert any("SIN" in error for error in result.errors)

    def test_validate_missing_min(self, validator, context, valid_message):
        """Test validation of message missing MIN property."""
        del valid_message["MIN"]
        result = validator.validate(valid_message, context)
        assert not result.is_valid
        assert any("MIN" in error for error in result.errors)

    def test_validate_missing_fields(self, validator, context, valid_message):
        """Test validation of message missing Fields property."""
        del valid_message["Fields"]
        result = validator.validate(valid_message, context)
        assert not result.is_valid
        assert any("Fields" in error for error in result.errors)

    def test_validate_invalid_sin_range(self, validator, context, valid_message):
        """Test validation of SIN outside valid range."""
        # Test below minimum
        valid_message["SIN"] = 15
        result = validator.validate(valid_message, context)
        assert not result.is_valid
        assert any("SIN" in error for error in result.errors)

        # Test above maximum
        valid_message["SIN"] = 256
        result = validator.validate(valid_message, context)
        assert not result.is_valid
        assert any("SIN" in error for error in result.errors)

    def test_validate_invalid_min_range(self, validator, context, valid_message):
        """Test validation of MIN outside valid range."""
        # Test below minimum
        valid_message["MIN"] = 0
        result = validator.validate(valid_message, context)
        assert not result.is_valid
        assert any("MIN" in error for error in result.errors)

        # Test above maximum
        valid_message["MIN"] = 256
        result = validator.validate(valid_message, context)
        assert not result.is_valid
        assert any("MIN" in error for error in result.errors)

    def test_validate_invalid_name_type(self, validator, context, valid_message):
        """Test validation when Name is not a string."""
        valid_message["Name"] = 123
        result = validator.validate(valid_message, context)
        assert not result.is_valid
        assert any("Name must be a string" in error for error in result.errors)

    def test_validate_invalid_fields_type(self, validator, context, valid_message):
        """Test validation when Fields is not an array."""
        valid_message["Fields"] = "not_an_array"
        result = validator.validate(valid_message, context)
        assert not result.is_valid
        assert any("must be an array" in error for error in result.errors)

    def test_validate_with_invalid_field(self, validator, context, valid_message):
        """Test validation with an invalid field in the Fields array."""
        valid_message["Fields"] = [{"invalid": "field"}]  # Missing required field properties
        result = validator.validate(valid_message, context)
        assert not result.is_valid
        assert any("Field validation error" in error for error in result.errors)

    def test_validate_empty_fields_array(self, validator, context, valid_message):
        """Test validation with empty Fields array."""
        valid_message["Fields"] = []
        result = validator.validate(valid_message, context)
        assert result.is_valid  # Empty arrays are valid according to spec
        assert not result.errors

    def test_validate_with_field_validation_error(self, validator, context, valid_message):
        """Test validation when field validation fails."""
        message = {
            "Name": "test_message",
            "SIN": 16,
            "MIN": 1,
            "Fields": [
                {
                    "Name": "test_field",
                    "Type": "unsignedint",
                    "Value": -1,  # Invalid value for unsigned int
                }
            ],
        }
        result = validator.validate(message, context)
        assert not result.is_valid
        assert any("Field validation error" in error for error in result.errors)

    def test_validate_with_empty_fields(
        self, validator: OGxMessageValidator, context: ValidationContext, valid_message
    ):
        """Test validation with empty fields array."""
        valid_message["Fields"] = []
        result = validator.validate(valid_message, context)
        assert result.is_valid
        assert not result.errors

    def test_validate_with_invalid_fields_array(
        self, validator: OGxMessageValidator, context: ValidationContext, valid_message
    ):
        """Test validation when Fields is not an array."""
        valid_message["Fields"] = "not_an_array"
        result = validator.validate(valid_message, context)
        assert not result.is_valid
        assert any("must be an array" in error for error in result.errors)

    def test_validate_with_field_validation_error_handling(
        self, validator: OGxMessageValidator, context: ValidationContext, valid_message
    ):
        """Test validation error handling when field validation fails."""
        valid_message["Fields"] = [
            {
                "Name": "test_field",
                "Type": "unsignedint",
                "Value": "not_a_number",  # Will cause ValueError in field validation
            }
        ]
        result = validator.validate(valid_message, context)
        assert not result.is_valid
        assert any("Field validation error" in error for error in result.errors)
        assert any("Invalid value for type" in error for error in result.errors)
