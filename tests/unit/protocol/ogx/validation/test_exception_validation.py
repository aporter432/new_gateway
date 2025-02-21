"""Unit tests for validation exceptions.

Tests custom exception types and their behaviors as defined in OGx-1.txt Section 5.1:
- ValidationError
- MessageValidationError
- ElementValidationError
- FieldValidationError

Error Message Formatting:
While OGx-1.txt doesn't mandate prefixes for all error types, it establishes a pattern
with Authentication/Encoding/Rate limit errors having clear prefixes. We extend this pattern
to all error types for:
- Consistent error identification
- Improved error tracing and debugging
- Better log readability
- Easier error filtering and handling
"""

from protocols.ogx.constants.error_codes import GatewayErrorCode
from protocols.ogx.validation.common.validation_exceptions import (
    ElementValidationError,
    FieldValidationError,
    MessageFilterValidationError,
    MessageValidationError,
    SizeValidationError,
    ValidationError,
)


class TestValidationExceptions:
    """Test validation exception behaviors per OGx-1.txt and best practices."""

    def test_validation_error_creation(self):
        """Test basic ValidationError creation and attributes."""
        error = ValidationError("Test error")
        assert str(error) == "Validation error: Test error"
        assert error.message == "Test error"
        assert error.error_code == GatewayErrorCode.VALIDATION_ERROR

        # Test with custom error code
        error = ValidationError("Custom error", GatewayErrorCode.INVALID_MESSAGE_FORMAT)
        assert str(error) == "Validation error: Custom error"
        assert error.error_code == GatewayErrorCode.INVALID_MESSAGE_FORMAT
        assert error.message == "Custom error"

    def test_message_validation_error(self):
        """Test MessageValidationError specific behavior."""
        error = MessageValidationError("Invalid message format")
        assert str(error) == "Validation error: Invalid message format"
        assert error.message == "Invalid message format"
        assert error.error_code == GatewayErrorCode.INVALID_MESSAGE_FORMAT

        # Test with custom error code
        error = MessageValidationError("Bad format", GatewayErrorCode.VALIDATION_ERROR)
        assert str(error) == "Validation error: Bad format"
        assert error.error_code == GatewayErrorCode.VALIDATION_ERROR

        # Test with context
        error = MessageValidationError("Missing field", context="SIN field")
        assert str(error) == "Validation error: Missing field (Context: SIN field)"
        assert error.context == "SIN field"

    def test_element_validation_error(self):
        """Test ElementValidationError specific behavior."""
        error = ElementValidationError("Invalid element")
        assert str(error) == "Validation error: Invalid element"
        assert error.message == "Invalid element"
        assert error.error_code == GatewayErrorCode.INVALID_ELEMENT_FORMAT

        # Test with index context
        error = ElementValidationError("Bad index", element_index=5)
        assert str(error) == "Validation error: Bad index at index 5"
        assert error.element_index == 5

        # Test with both context and index
        error = ElementValidationError("Missing field", context="Fields array", element_index=2)
        assert str(error) == "Validation error: Missing field at index 2 (Fields array)"
        assert "Fields array" in str(error)
        assert "index 2" in str(error)

    def test_field_validation_error(self):
        """Test FieldValidationError specific behavior."""
        error = FieldValidationError("Invalid field value")
        assert str(error) == "Validation error: Invalid field value"
        assert error.message == "Invalid field value"
        assert error.error_code == GatewayErrorCode.INVALID_FIELD_FORMAT

        # Test with field name context
        error = FieldValidationError("Bad value", field_name="temperature")
        assert str(error) == "Validation error: Bad value in field 'temperature'"
        assert error.field_name == "temperature"

    def test_message_filter_validation_error(self):
        """Test MessageFilterValidationError specific behavior."""
        error = MessageFilterValidationError("Invalid filter")
        assert str(error) == "Validation error: Invalid filter"
        assert error.message == "Invalid filter"
        assert error.error_code == GatewayErrorCode.INVALID_MESSAGE_FILTER

        # Test with filter details
        error = MessageFilterValidationError("Bad date range", filter_details="FromDate > ToDate")
        assert str(error) == "Validation error: Bad date range (FromDate > ToDate)"
        assert error.filter_details == "FromDate > ToDate"

    def test_size_validation_error(self):
        """Test SizeValidationError specific behavior."""
        error = SizeValidationError("Message too large")
        assert str(error) == "Validation error: Message too large"
        assert error.message == "Message too large"
        assert error.error_code == GatewayErrorCode.MESSAGE_SIZE_EXCEEDED

        # Test with size details
        error = SizeValidationError("Message too large", current_size=1024, max_size=1000)
        assert str(error) == "Validation error: Message too large (size: 1024, max: 1000)"
        assert error.current_size == 1024
        assert error.max_size == 1000

    def test_validation_error_with_details(self):
        """Test validation error with additional details."""
        error = ValidationError(
            "Invalid format",
            details={"field": "temperature", "expected": "number", "got": "string"},
        )
        assert (
            str(error)
            == "Validation error: Invalid format (field=temperature, expected=number, got=string)"
        )
        assert error.details == {"field": "temperature", "expected": "number", "got": "string"}

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
            assert str(error) == "Validation error: Wrapped error"
            assert error.__cause__ == e

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
            assert str(error).startswith("Validation error:")
