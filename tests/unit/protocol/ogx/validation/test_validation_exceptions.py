"""Unit tests for validation exceptions.

Tests focus on exception-specific behavior, inheritance, and initialization.
Field/message/element validation tests are handled in their respective test files.
"""

# ruff: noqa: E731, E501
# pylint: disable=too-many-public-methods,protected-access
# pylint: disable=attribute-defined-outside-init
# pylint: disable=missing-docstring,invalid-name
# pylint: disable=no-member

from protocols.ogx.constants.error_codes import GatewayErrorCode, HTTPErrorCode
from protocols.ogx.validation.common.validation_exceptions import (
    AuthenticationError,
    ElementValidationError,
    EncodingError,
    FieldValidationError,
    MessageFilterValidationError,
    MessageValidationError,
    OGxProtocolError,
    ProtocolError,
    RateLimitError,
    SizeValidationError,
    ValidationError,
)


class TestValidationExceptions:
    """Test validation exception behaviors."""

    def test_base_protocol_error_initialization(self):
        """Test OGxProtocolError initialization and attributes."""
        # Test with no error code
        error = OGxProtocolError("test")
        assert error.args == ("test",)
        assert error.error_code is None
        assert error._original_message == "test"
        assert isinstance(error, Exception)

        # Test with error code
        error = OGxProtocolError("test", 1001)
        assert error.args == ("test",)
        assert error.error_code == 1001
        assert error._original_message == "test"

        # Test with empty message
        error = OGxProtocolError("")
        assert error.args == ("",)
        assert error.error_code is None
        assert error._original_message == ""

    def test_protocol_error_initialization(self):
        """Test ProtocolError initialization and formatting."""
        # Test with default error code
        error = ProtocolError("test")
        assert error.args == ("Protocol error: test",)
        assert error.error_code == GatewayErrorCode.SUBMIT_MESSAGE_RATE_EXCEEDED
        assert error._original_message == "test"

        # Test with custom error code
        error = ProtocolError("test", 1001)
        assert error.args == ("Protocol error: test",)
        assert error.error_code == 1001
        assert error._original_message == "test"

    def test_error_pickling(self):
        """Test validation errors can be pickled/unpickled."""
        import pickle

        # Test all error types
        errors = [
            ValidationError("Test"),
            MessageValidationError("Test", context="Context"),
            ElementValidationError("Test", element_index=1),
            FieldValidationError("Test", field_name="field"),
            MessageFilterValidationError("Test", filter_details="details"),
            SizeValidationError("Test", current_size=100, max_size=200),
            AuthenticationError("Test"),
            EncodingError("Test"),
            RateLimitError("Test"),
        ]

        for error in errors:
            # Pickle and unpickle
            pickled = pickle.dumps(error)
            unpickled = pickle.loads(pickled)

            # Verify properties are preserved
            assert str(unpickled) == str(error)
            assert unpickled.error_code == error.error_code

    def test_exception_inheritance(self):
        """Test exception inheritance relationships."""
        # Test base inheritance
        assert issubclass(OGxProtocolError, Exception)
        assert issubclass(ValidationError, Exception)
        assert issubclass(ProtocolError, OGxProtocolError)

        # Test validation error hierarchy
        assert issubclass(MessageValidationError, ValidationError)
        assert issubclass(ElementValidationError, ValidationError)
        assert issubclass(FieldValidationError, ValidationError)
        assert issubclass(MessageFilterValidationError, ValidationError)
        assert issubclass(SizeValidationError, ValidationError)

        # Test protocol error hierarchy
        assert issubclass(AuthenticationError, OGxProtocolError)
        assert issubclass(EncodingError, OGxProtocolError)
        assert issubclass(RateLimitError, OGxProtocolError)

    def test_exception_with_cause(self):
        """Test exception chaining with cause."""
        try:
            raise ValueError("Original error")
        except ValueError as e:
            error = ValidationError("Wrapped error", cause=e)
            assert str(error) == "Wrapped error"
            assert error.__cause__ == e
            assert isinstance(error.__cause__, ValueError)

    def test_multiple_validation_errors(self):
        """Test handling multiple validation errors."""
        errors = [
            ValidationError("Error 1"),
            MessageValidationError("Error 2", context="Context"),
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
        assert "Context" in combined
        assert "test" in combined

    def test_error_code_defaults(self):
        """Test default error codes for each exception type."""
        test_cases = [
            (ValidationError, GatewayErrorCode.VALIDATION_ERROR),
            (MessageValidationError, GatewayErrorCode.INVALID_MESSAGE_FORMAT),
            (ElementValidationError, GatewayErrorCode.INVALID_ELEMENT_FORMAT),
            (FieldValidationError, GatewayErrorCode.INVALID_FIELD_FORMAT),
            (MessageFilterValidationError, GatewayErrorCode.INVALID_MESSAGE_FILTER),
            (SizeValidationError, GatewayErrorCode.MESSAGE_SIZE_EXCEEDED),
            (AuthenticationError, HTTPErrorCode.UNAUTHORIZED),
            (EncodingError, GatewayErrorCode.INVALID_MESSAGE_FORMAT),
            (RateLimitError, HTTPErrorCode.TOO_MANY_REQUESTS),
        ]

        for error_class, default_code in test_cases:
            error = error_class("test")
            assert error.error_code == default_code

    def test_error_message_formatting(self):
        """Test error message formatting for all exception types."""
        test_cases = [
            (ValidationError("test"), "test"),
            (MessageValidationError("test", context="ctx"), "test (Context: ctx)"),
            (ElementValidationError("test", element_index=1), "test at index 1"),
            (FieldValidationError("test", field_name="field"), "test in field 'field'"),
            (MessageFilterValidationError("test", filter_details="details"), "test (details)"),
            (
                SizeValidationError("test", current_size=100, max_size=200),
                "test (size: 100, max: 200)",
            ),
            (AuthenticationError("test"), "Authentication error: test"),
            (EncodingError("test"), "Encoding error: test"),
            (RateLimitError("test"), "Rate limit error: test"),
        ]

        for error, expected_message in test_cases:
            assert str(error) == expected_message
