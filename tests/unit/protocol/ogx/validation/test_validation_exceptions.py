"""Unit tests for validation exceptions.

Tests focus on exception-specific behavior, inheritance, and initialization.
Field/message/element validation tests are handled in their respective test files.

Error Message Formatting:
While OGx-1.txt doesn't mandate prefixes for all error types, it establishes a pattern
with Authentication/Encoding/Rate limit errors having clear prefixes. We extend this pattern
to all error types for:
- Consistent error identification
- Improved error tracing and debugging
- Better log readability
- Easier error filtering and handling
"""

# ruff: noqa: E731, E501
# pylint: disable=too-many-public-methods,protected-access
# pylint: disable=attribute-defined-outside-init
# pylint: disable=missing-docstring,invalid-name
# pylint: disable=no-member

from Protexis_Command.api.config.http_error_codes import HTTPErrorCode
from Protexis_Command.protocols.ogx.constants.ogx_error_codes import GatewayErrorCode
from Protexis_Command.protocols.ogx.validation.ogx_validation_exceptions import (
    AuthenticationError,
    ElementValidationError,
    EncodingError,
    FieldValidationError,
    MessageFilterValidationError,
    MessageValidationError,
    RateLimitError,
    SizeValidationError,
    ValidationError,
)


class TestValidationExceptions:
    """Test validation exception behaviors per OGx-1.txt and best practices."""

    def test_base_protocol_error_initialization(self):
        """Test base protocol error initialization."""
        error = ValidationError("test")
        assert str(error) == "Validation error: test"
        assert error.error_code == GatewayErrorCode.VALIDATION_ERROR

    def test_protocol_error_initialization(self):
        """Test protocol error initialization with code."""
        error = ValidationError("test", GatewayErrorCode.INVALID_MESSAGE_FORMAT)
        assert str(error) == "Validation error: test"
        assert error.error_code == GatewayErrorCode.INVALID_MESSAGE_FORMAT

    def test_error_pickling(self):
        """Test error can be pickled/unpickled."""
        import pickle

        error = ValidationError("test", GatewayErrorCode.VALIDATION_ERROR)
        pickled = pickle.dumps(error)
        unpickled = pickle.loads(pickled)
        assert str(unpickled) == str(error)
        assert unpickled.error_code == error.error_code

    def test_exception_inheritance(self):
        """Test exception inheritance relationships."""
        assert issubclass(MessageValidationError, ValidationError)
        assert issubclass(ElementValidationError, ValidationError)
        assert issubclass(FieldValidationError, ValidationError)
        assert issubclass(MessageFilterValidationError, ValidationError)
        assert issubclass(SizeValidationError, ValidationError)

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
            # Ensure consistent error prefix pattern
            assert str(error).startswith("Validation error:")

    def test_error_code_defaults(self):
        """Test default error codes for each exception type per OGx-1.txt."""
        test_cases = [
            (ValidationError, GatewayErrorCode.VALIDATION_ERROR),  # 10000
            (MessageValidationError, GatewayErrorCode.INVALID_MESSAGE_FORMAT),  # 10001
            (ElementValidationError, GatewayErrorCode.INVALID_ELEMENT_FORMAT),  # 10002
            (FieldValidationError, GatewayErrorCode.INVALID_FIELD_FORMAT),  # 10003
            (MessageFilterValidationError, GatewayErrorCode.INVALID_MESSAGE_FILTER),  # 10004
            (SizeValidationError, GatewayErrorCode.MESSAGE_SIZE_EXCEEDED),  # 10005
            (AuthenticationError, HTTPErrorCode.UNAUTHORIZED),  # 401
            (EncodingError, GatewayErrorCode.ENCODE_ERROR),  # 26002
            (RateLimitError, HTTPErrorCode.TOO_MANY_REQUESTS),  # 429
        ]

        for error_class, default_code in test_cases:
            error = error_class("test")
            assert (
                error.error_code == default_code
            ), f"Expected {error_class.__name__} to have code {default_code}"

    def test_error_message_formatting(self):
        """Test error message formatting for consistency and clarity.

        While OGx-1.txt only explicitly defines some error prefixes,
        we maintain a consistent prefix pattern across all error types
        to improve error handling and debugging.
        """
        test_cases = [
            (ValidationError("test"), "Validation error: test"),
            (
                MessageValidationError("test", context="ctx"),
                "Validation error: test (Context: ctx)",
            ),
            (ElementValidationError("test", element_index=1), "Validation error: test at index 1"),
            (
                FieldValidationError("test", field_name="field"),
                "Validation error: test in field 'field'",
            ),
            (
                MessageFilterValidationError("test", filter_details="details"),
                "Validation error: test (details)",
            ),
            (
                SizeValidationError("test", current_size=100, max_size=200),
                "Validation error: test (size: 100, max: 200)",
            ),
            # These prefixes are explicitly defined in OGx-1.txt
            (AuthenticationError("test"), "Authentication error: test"),
            (EncodingError("test"), "Encoding error: test"),
            (RateLimitError("test"), "Rate limit error: test"),
        ]

        for error, expected_message in test_cases:
            assert (
                str(error) == expected_message
            ), f"Expected {error.__class__.__name__} to format message as '{expected_message}'"
