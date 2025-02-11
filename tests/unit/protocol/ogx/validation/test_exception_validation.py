"""Unit tests for validation exceptions.

Tests custom exception types and their behaviors:
- ValidationError  
- MessageValidationError
- ElementValidationError
- FieldValidationError
"""

import pytest

from protocols.ogx.validation.common.validation_exceptions import (
    ValidationError,
    MessageValidationError,
    ElementValidationError,
    FieldValidationError,
    MessageFilterValidationError,
    SizeValidationError,
)
from protocols.ogx.constants.error_codes import GatewayErrorCode


class TestValidationExceptions:
    """Test validation exception behaviors."""

    def test_validation_error_creation(self):
        """Test basic ValidationError creation and attributes."""
        error = ValidationError("Test error")
        assert str(error) == "Test error"
        assert error.message == "Test error"
        assert error.error_code == GatewayErrorCode.VALIDATION_ERROR

        # Test with custom error code
        error = ValidationError("Custom error", GatewayErrorCode.INVALID_MESSAGE_FORMAT)
        assert error.error_code == GatewayErrorCode.INVALID_MESSAGE_FORMAT
        assert error.message == "Custom error"

    def test_message_validation_error(self):
        """Test MessageValidationError specific behavior."""
        error = MessageValidationError("Invalid message format")
        assert str(error) == "Invalid message format"
        assert error.message == "Invalid message format"
        assert error.error_code == GatewayErrorCode.INVALID_MESSAGE_FORMAT

        # Test with custom error code
        error = MessageValidationError("Bad format", GatewayErrorCode.VALIDATION_ERROR)
        assert error.error_code == GatewayErrorCode.VALIDATION_ERROR

        # Test with context
        error = MessageValidationError("Missing field", context="SIN field")
        assert "SIN field" in str(error)
        assert error.context == "SIN field"

    def test_element_validation_error(self):
        """Test ElementValidationError specific behavior."""
        error = ElementValidationError("Invalid element")
        assert str(error) == "Invalid element"
        assert error.message == "Invalid element"
        assert error.error_code == GatewayErrorCode.INVALID_ELEMENT_FORMAT

        # Test with index context
        error = ElementValidationError("Bad index", element_index=5)
        assert "index 5" in str(error)
        assert error.element_index == 5

        # Test with both context and index
        error = ElementValidationError("Missing field", context="Fields array", element_index=2)
        assert "Fields array" in str(error)
        assert "index 2" in str(error)

    def test_field_validation_error(self):
        """Test FieldValidationError specific behavior."""
        error = FieldValidationError("Invalid field value")
        assert str(error) == "Invalid field value"
        assert error.message == "Invalid field value"
        assert error.error_code == GatewayErrorCode.INVALID_FIELD_FORMAT

        # Test with field name context
        error = FieldValidationError("Bad value", field_name="temperature")
        assert "temperature" in str(error)
        assert error.field_name == "temperature"

    def test_message_filter_validation_error(self):
        """Test MessageFilterValidationError specific behavior."""
        error = MessageFilterValidationError("Invalid filter")
        assert str(error) == "Invalid filter"
        assert error.message == "Invalid filter"
        assert error.error_code == GatewayErrorCode.INVALID_MESSAGE_FILTER

        # Test with filter details
        error = MessageFilterValidationError("Bad date range", filter_details="FromDate > ToDate")
        assert "FromDate > ToDate" in str(error)
        assert error.filter_details == "FromDate > ToDate"

    def test_size_validation_error(self):
        """Test SizeValidationError specific behavior."""
        error = SizeValidationError("Message too large")
        assert str(error) == "Message too large"
        assert error.message == "Message too large"
        assert error.error_code == GatewayErrorCode.MESSAGE_SIZE_EXCEEDED

        # Test with size details
        error = SizeValidationError("Exceeds limit", current_size=1500, max_size=1000)
        assert "1500" in str(error)
        assert "1000" in str(error)
        assert error.current_size == 1500
        assert error.max_size == 1000

    def test_exception_inheritance(self):
        """Test exception inheritance relationships."""
        # All should inherit from ValidationError
        assert issubclass(MessageValidationError, ValidationError)
        assert issubclass(ElementValidationError, ValidationError)
        assert issubclass(FieldValidationError, ValidationError)
        assert issubclass(MessageFilterValidationError, ValidationError)
        assert issubclass(SizeValidationError, ValidationError)

        # Test isinstance behavior
        error = MessageValidationError("test")
        assert isinstance(error, ValidationError)
        assert isinstance(error, MessageValidationError)
        assert not isinstance(error, ElementValidationError)

    def test_exception_with_cause(self):
        """Test exception chaining with cause."""
        try:
            raise ValueError("Original error")
        except ValueError as e:
            error = ValidationError("Wrapped error", cause=e)
            assert str(error) == "Wrapped error"
            assert error.__cause__ == e

    def test_validation_error_with_details(self):
        """Test ValidationError with additional details."""
        details = {"field": "temperature", "value": -999, "limit": 0}
        error = ValidationError("Invalid temperature", details=details)
        assert error.details == details
        assert "temperature" in str(error)
        assert "-999" in str(error)

    def test_multiple_validation_errors(self):
        """Test handling multiple validation errors."""
        errors = [
            ValidationError("Error 1"),
            MessageValidationError("Error 2"),
            FieldValidationError("Error 3", field_name="test"),
        ]

        # Verify each error maintains its properties
        for error in errors:
            assert isinstance(error, ValidationError)
            assert error.message in str(error)
            assert error.error_code is not None

        # Test combining error messages
        combined = " | ".join(str(err) for err in errors)
        assert "Error 1" in combined
        assert "Error 2" in combined
        assert "Error 3" in combined
