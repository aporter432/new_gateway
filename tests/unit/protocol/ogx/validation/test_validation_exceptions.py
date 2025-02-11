"""Unit tests for validation exceptions."""

# ruff: noqa: E731, E501
# pylint: disable=too-many-public-methods,protected-access
# pylint: disable=attribute-defined-outside-init
# pylint: disable=missing-docstring,invalid-name
# pylint: disable=no-member

import pytest
from protocols.ogx.constants.error_codes import GatewayErrorCode, HTTPErrorCode
from protocols.ogx.validation.common.validation_exceptions import (
    OGxProtocolError,
    ProtocolError,
    ValidationError,
    MessageValidationError,
    ElementValidationError,
    FieldValidationError,
    MessageFilterValidationError,
    SizeValidationError,
    AuthenticationError,
    EncodingError,
    RateLimitError,
)


class TestValidationExceptions:
    """Test validation exception behaviors."""

    def test_ogx_protocol_error(self):
        """Test OGxProtocolError creation and attributes."""
        error = OGxProtocolError("Test error", 1001)
        assert str(error) == "Test error"
        assert error.error_code == 1001

        # Test without error code
        error = OGxProtocolError("Test error")
        assert error.error_code is None

    def test_ogx_protocol_error_str_and_repr(self):
        """Test OGxProtocolError str and repr methods."""
        error = OGxProtocolError("Test error", 1001)
        assert str(error) == "Test error"
        assert repr(error) == "OGxProtocolError('Test error', 1001)"

        error = OGxProtocolError("Test error")  # No error code
        assert repr(error) == "OGxProtocolError('Test error', None)"

    def test_protocol_error(self):
        """Test ProtocolError creation and attributes."""
        error = ProtocolError("Test error", 1001)
        assert "Protocol error: Test error" in str(error)
        assert error.error_code == 1001

        # Test with default error code
        error = ProtocolError("Test error")
        assert error.error_code == GatewayErrorCode.SUBMIT_MESSAGE_RATE_EXCEEDED

    def test_protocol_error_with_default_code(self):
        """Test ProtocolError with default error code behavior."""
        error = ProtocolError("Test error")
        assert str(error) == "Protocol error: Test error"
        assert (
            repr(error)
            == f"ProtocolError('Test error', {GatewayErrorCode.SUBMIT_MESSAGE_RATE_EXCEEDED})"
        )

    def test_validation_error(self):
        """Test ValidationError creation and attributes."""
        details = {"field": "test", "value": 123}
        error = ValidationError(
            "Test error",
            GatewayErrorCode.VALIDATION_ERROR,
            cause=ValueError("Root cause"),
            details=details,
        )
        assert error.message == "Test error"
        assert error.error_code == GatewayErrorCode.VALIDATION_ERROR
        assert isinstance(error.cause, ValueError)
        assert error.details == details

        # Test with minimal args
        error = ValidationError("Test error")
        assert error.details == {}
        assert error.cause is None

    def test_validation_error_with_cause_chain(self):
        """Test ValidationError with exception chaining."""
        root_cause = ValueError("Root error")
        error = ValidationError("Test error", GatewayErrorCode.VALIDATION_ERROR, cause=root_cause)
        assert str(error) == "Test error"
        assert error.__cause__ == root_cause
        assert repr(error) == "ValidationError('Test error', 10000)"

    def test_validation_error_detailed_output(self):
        """Test ValidationError with detailed error output."""
        details = {"field": "temperature", "value": -999, "limit": 0, "additional": "info"}
        error = ValidationError("Test error", details=details)
        error_str = str(error)
        assert "Test error" in error_str
        assert "temperature" in error_str
        assert "-999" in error_str
        assert "additional" in error_str

    def test_message_validation_error(self):
        """Test MessageValidationError creation and attributes."""
        error = MessageValidationError(
            "Test error", GatewayErrorCode.INVALID_MESSAGE_FORMAT, context="SIN validation"
        )
        assert "Test error" in str(error)
        assert "SIN validation" in str(error)
        assert error.context == "SIN validation"

        # Test without context
        error = MessageValidationError("Test error")
        assert str(error) == "Test error"
        assert error.context is None

    def test_message_validation_error_complex_context(self):
        """Test MessageValidationError with complex context information."""
        error = MessageValidationError(
            "Field validation failed",
            GatewayErrorCode.INVALID_MESSAGE_FORMAT,
            context="SIN: 16, MIN: 2, Field: temperature",
        )
        assert "Field validation failed" in str(error)
        assert "SIN: 16" in str(error)
        assert (
            repr(error)
            == "MessageValidationError('Field validation failed', 10001, 'SIN: 16, MIN: 2, Field: temperature')"
        )

    def test_element_validation_error(self):
        """Test ElementValidationError creation and attributes."""
        error = ElementValidationError("Test error", element_index=5, context="Array validation")
        assert "Test error" in str(error)
        assert "index 5" in str(error)
        assert "Array validation" in str(error)

        # Test minimal construction
        error = ElementValidationError("Test error")
        assert str(error) == "Test error"
        assert error.element_index is None
        assert error.context is None

    def test_element_validation_error_complex(self):
        """Test ElementValidationError with index and context."""
        error = ElementValidationError(
            "Invalid element structure", element_index=5, context="Array validation at position 5"
        )
        assert "Invalid element structure" in str(error)
        assert "index 5" in str(error)
        assert "Array validation" in str(error)
        assert (
            repr(error)
            == "ElementValidationError('Invalid element structure', 5, 'Array validation at position 5')"
        )

    def test_field_validation_error(self):
        """Test FieldValidationError creation and attributes."""
        error = FieldValidationError("Test error", field_name="temperature")
        assert "temperature" in str(error)
        assert error.field_name == "temperature"

        # Test without field name
        error = FieldValidationError("Test error")
        assert str(error) == "Test error"
        assert error.field_name is None

    def test_message_filter_validation_error(self):
        """Test MessageFilterValidationError creation and attributes."""
        error = MessageFilterValidationError("Test error", filter_details="Date range invalid")
        assert "Test error" in str(error)
        assert "Date range invalid" in str(error)
        assert error.filter_details == "Date range invalid"

        # Test without details
        error = MessageFilterValidationError("Test error")
        assert str(error) == "Test error"
        assert error.filter_details is None

    def test_message_filter_validation_error_details(self):
        """Test MessageFilterValidationError with detailed filter information."""
        error = MessageFilterValidationError(
            "Invalid filter expression",
            filter_details="Field 'timestamp' has invalid date format YYYY-MM-DD",
        )
        assert "Invalid filter expression" in str(error)
        assert "timestamp" in str(error)
        assert "YYYY-MM-DD" in str(error)
        assert (
            repr(error)
            == "MessageFilterValidationError('Invalid filter expression', 'Field \\'timestamp\\' has invalid date format YYYY-MM-DD')"
        )

    def test_size_validation_error(self):
        """Test SizeValidationError creation and attributes."""
        error = SizeValidationError("Test error", current_size=1500, max_size=1000)
        assert "1500" in str(error)
        assert "1000" in str(error)
        assert error.current_size == 1500
        assert error.max_size == 1000

        # Test without sizes
        error = SizeValidationError("Test error")
        assert str(error) == "Test error"
        assert error.current_size is None
        assert error.max_size is None

    def test_size_validation_error_boundary(self):
        """Test SizeValidationError at boundary conditions."""
        # Test maximum size
        error = SizeValidationError("Message too large", current_size=65535, max_size=65536)
        assert "65535" in str(error)
        assert "65536" in str(error)
        assert repr(error) == "SizeValidationError('Message too large', 65535, 65536)"

        # Test zero size
        error = SizeValidationError("Empty message", current_size=0, max_size=1024)
        assert "0" in str(error)
        assert "1024" in str(error)

    def test_authentication_error(self):
        """Test AuthenticationError creation and attributes."""
        error = AuthenticationError("Invalid token", 401)
        assert "Authentication error: Invalid token" in str(error)
        assert error.error_code == 401

        # Test with default error code
        error = AuthenticationError("Invalid token")
        assert error.error_code == 401  # Should use default UNAUTHORIZED code

    def test_encoding_error(self):
        """Test EncodingError creation and attributes."""
        error = EncodingError("Invalid format", 1001)
        assert "Encoding error: Invalid format" in str(error)
        assert error.error_code == 1001

        # Test with default error code
        error = EncodingError("Invalid format")
        assert error.error_code == GatewayErrorCode.INVALID_MESSAGE_FORMAT

    def test_rate_limit_error(self):
        """Test RateLimitError creation and attributes."""
        error = RateLimitError("Too many requests", 429)
        assert "Rate limit error: Too many requests" in str(error)
        assert error.error_code == 429

        # Test with default error code
        error = RateLimitError("Too many requests")
        assert error.error_code == 429  # Should use default TOO_MANY_REQUESTS code

    def test_exception_inheritance(self):
        """Test exception inheritance relationships."""
        # All should inherit from OGxProtocolError
        assert issubclass(ValidationError, Exception)
        assert issubclass(MessageValidationError, ValidationError)
        assert issubclass(ElementValidationError, ValidationError)
        assert issubclass(FieldValidationError, ValidationError)
        assert issubclass(MessageFilterValidationError, ValidationError)
        assert issubclass(SizeValidationError, ValidationError)
        assert issubclass(AuthenticationError, OGxProtocolError)
        assert issubclass(EncodingError, OGxProtocolError)
        assert issubclass(RateLimitError, OGxProtocolError)

    def test_error_subclassing_behavior(self):
        """Test error class inheritance behaviors."""

        # Test base error class can be subclassed
        class CustomValidationError(ValidationError):
            def __init__(self, msg):
                super().__init__(msg, GatewayErrorCode.VALIDATION_ERROR)

        error = CustomValidationError("Custom error")
        assert isinstance(error, ValidationError)
        assert isinstance(error, Exception)
        assert error.error_code == GatewayErrorCode.VALIDATION_ERROR

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

    def test_error_code_inheritance(self):
        """Test error code inheritance and overrides."""
        # Test ValidationError with explicit code
        error = ValidationError("Test", GatewayErrorCode.INVALID_FIELD_TYPE)
        assert error.error_code == GatewayErrorCode.INVALID_FIELD_TYPE

        # Test MessageValidationError default code
        error = MessageValidationError("Test")
        assert error.error_code == GatewayErrorCode.INVALID_MESSAGE_FORMAT

        # Test ElementValidationError default code
        error = ElementValidationError("Test")
        assert error.error_code == GatewayErrorCode.INVALID_ELEMENT_FORMAT

        # Test override of default code
        error = MessageValidationError("Test", GatewayErrorCode.VALIDATION_ERROR)
        assert error.error_code == GatewayErrorCode.VALIDATION_ERROR

    def test_protocol_errors_with_default_codes(self):
        """Test protocol errors using default error codes."""
        # Test AuthenticationError default code
        error = AuthenticationError("Invalid credentials")
        assert error.error_code == HTTPErrorCode.UNAUTHORIZED
        assert str(error) == "Authentication error: Invalid credentials"
        assert repr(error) == "AuthenticationError('Invalid credentials', 401)"

        # Test EncodingError default code
        error = EncodingError("Invalid format")
        assert error.error_code == GatewayErrorCode.INVALID_MESSAGE_FORMAT
        assert str(error) == "Encoding error: Invalid format"
        assert (
            repr(error)
            == f"EncodingError('Invalid format', {GatewayErrorCode.INVALID_MESSAGE_FORMAT})"
        )

        # Test RateLimitError default code
        error = RateLimitError("Too many requests")
        assert error.error_code == HTTPErrorCode.TOO_MANY_REQUESTS
        assert str(error) == "Rate limit error: Too many requests"
        assert repr(error) == "RateLimitError('Too many requests', 429)"

    def test_protocol_errors_with_custom_codes(self):
        """Test protocol errors with custom error codes."""
        # Test AuthenticationError with custom code
        error = AuthenticationError("Custom auth error", 403)
        assert error.error_code == 403
        assert str(error) == "Authentication error: Custom auth error"

        # Test EncodingError with custom code
        error = EncodingError("Custom encoding error", 1001)
        assert error.error_code == 1001
        assert str(error) == "Encoding error: Custom encoding error"

        # Test RateLimitError with custom code
        error = RateLimitError("Custom rate limit error", 503)
        assert error.error_code == 503
        assert str(error) == "Rate limit error: Custom rate limit error"

    def test_http_error_codes(self):
        """Test HTTP error code handling."""
        # Test authentication error with default code
        error = AuthenticationError("Invalid credentials")
        assert error.error_code == HTTPErrorCode.UNAUTHORIZED
        assert str(error) == "Authentication error: Invalid credentials"

        # Test rate limit error with default code
        error = RateLimitError("Too many requests")
        assert error.error_code == HTTPErrorCode.TOO_MANY_REQUESTS
        assert str(error) == "Rate limit error: Too many requests"

        # Test forbidden error
        error = AuthenticationError("Not authorized", HTTPErrorCode.FORBIDDEN)
        assert error.error_code == HTTPErrorCode.FORBIDDEN
        assert str(error) == "Authentication error: Not authorized"

        # Test service unavailable
        error = RateLimitError("Service down", HTTPErrorCode.SERVICE_UNAVAILABLE)
        assert error.error_code == HTTPErrorCode.SERVICE_UNAVAILABLE
        assert str(error) == "Rate limit error: Service down"

    def test_protocol_error_default_code_with_str_and_repr(self):
        """Test protocol error with default code and string/repr methods."""
        # Test lines 17-18 (OGxProtocolError)
        error = OGxProtocolError("Test error")
        assert str(error) == "Test error"
        assert repr(error) == "OGxProtocolError('Test error', None)"

        # Test lines 25-26 (ProtocolError)
        error = ProtocolError("Test error")
        assert str(error) == "Protocol error: Test error"
        assert (
            repr(error)
            == f"ProtocolError('Test error', {GatewayErrorCode.SUBMIT_MESSAGE_RATE_EXCEEDED})"
        )

    def test_protocol_specific_errors_complete_coverage(self):
        """Test protocol specific error classes for complete coverage."""
        # Test lines 194-196 (AuthenticationError)
        auth_error = AuthenticationError("Invalid token")
        assert auth_error.error_code == HTTPErrorCode.UNAUTHORIZED
        assert str(auth_error) == "Authentication error: Invalid token"
        assert repr(auth_error) == "AuthenticationError('Invalid token', 401)"

        # Test lines 203-205 (EncodingError)
        encoding_error = EncodingError("Bad format")
        assert encoding_error.error_code == GatewayErrorCode.INVALID_MESSAGE_FORMAT
        assert str(encoding_error) == "Encoding error: Bad format"
        assert (
            repr(encoding_error)
            == f"EncodingError('Bad format', {GatewayErrorCode.INVALID_MESSAGE_FORMAT})"
        )

        # Test lines 212-214 (RateLimitError)
        rate_limit_error = RateLimitError("Too many requests")
        assert rate_limit_error.error_code == HTTPErrorCode.TOO_MANY_REQUESTS
        assert str(rate_limit_error) == "Rate limit error: Too many requests"
        assert repr(rate_limit_error) == "RateLimitError('Too many requests', 429)"

    def test_protocol_error_inheritance_and_defaults(self):
        """Test protocol error inheritance and default behaviors."""
        # Test complete inheritance chain
        auth_error = AuthenticationError("Test")
        assert isinstance(auth_error, OGxProtocolError)
        assert issubclass(AuthenticationError, OGxProtocolError)

        encoding_error = EncodingError("Test")
        assert isinstance(encoding_error, OGxProtocolError)
        assert issubclass(EncodingError, OGxProtocolError)

        rate_error = RateLimitError("Test")
        assert isinstance(rate_error, OGxProtocolError)
        assert issubclass(RateLimitError, OGxProtocolError)

    def test_protocol_error_custom_codes(self):
        """Test protocol errors with custom error codes."""
        # Test custom codes for all protocol errors
        auth_error = AuthenticationError("Test", 403)  # Custom forbidden code
        assert auth_error.error_code == 403

        encoding_error = EncodingError("Test", 1001)  # Custom format code
        assert encoding_error.error_code == 1001

        rate_error = RateLimitError("Test", 503)  # Custom service unavailable code
        assert rate_error.error_code == 503

    def test_protocol_error_string_formatting(self):
        """Test protocol error string formatting edge cases."""
        # Test string formatting with different message types
        auth_error = AuthenticationError("")  # Empty message
        assert str(auth_error) == "Authentication error: "

        encoding_error = EncodingError("Test\nMultiline\nError")  # Multiline message
        assert "Test\nMultiline\nError" in str(encoding_error)

        rate_error = RateLimitError("Error with spaces  ")  # Extra spaces
        assert str(rate_error) == "Rate limit error: Error with spaces  "

    def test_protocol_base_errors(self):
        """Test base protocol error classes (lines 17-18, 25-26)."""
        # Test __init__ of OGxProtocolError (lines 17-18)
        base_error = OGxProtocolError("Base error")
        assert base_error.error_code is None
        assert str(base_error) == "Base error"

        # Test __init__ of ProtocolError (lines 25-26)
        proto_error = ProtocolError("Proto error")
        assert proto_error.error_code == GatewayErrorCode.SUBMIT_MESSAGE_RATE_EXCEEDED
        assert str(proto_error) == "Protocol error: Proto error"

    def test_auth_encoding_rate_errors(self):
        """Test specific protocol error classes (lines 194-196, 203-205, 212-214)."""
        # Test AuthenticationError __init__ (lines 194-196)
        auth_error = AuthenticationError("Auth failed")
        assert auth_error.error_code == HTTPErrorCode.UNAUTHORIZED
        assert isinstance(auth_error, OGxProtocolError)
        assert str(auth_error) == "Authentication error: Auth failed"

        # Test EncodingError __init__ (lines 203-205)
        encoding_error = EncodingError("Bad encoding")
        assert encoding_error.error_code == GatewayErrorCode.INVALID_MESSAGE_FORMAT
        assert isinstance(encoding_error, OGxProtocolError)
        assert str(encoding_error) == "Encoding error: Bad encoding"

        # Test RateLimitError __init__ (lines 212-214)
        rate_error = RateLimitError("Too fast")
        assert rate_error.error_code == HTTPErrorCode.TOO_MANY_REQUESTS
        assert isinstance(rate_error, OGxProtocolError)
        assert str(rate_error) == "Rate limit error: Too fast"

    def test_protocol_base_init_coverage(self):
        """Test base protocol error initialization (lines 17-18, 25-26)."""
        # Test OGxProtocolError init (lines 17-18)
        base_error = OGxProtocolError("Test message")
        assert base_error.error_code is None
        assert base_error.args == ("Test message",)

        # Test ProtocolError init (lines 25-26)
        proto_error = ProtocolError("Test message")
        assert proto_error.error_code == GatewayErrorCode.SUBMIT_MESSAGE_RATE_EXCEEDED
        assert proto_error.args == ("Protocol error: Test message",)

    def test_specific_errors_init_coverage(self):
        """Test specific error class initialization (lines 194-196, 203-205, 212-214)."""
        # Test AuthenticationError init (lines 194-196)
        auth_error = AuthenticationError("Auth failed")
        assert auth_error.error_code == HTTPErrorCode.UNAUTHORIZED
        assert auth_error.args == ("Authentication error: Auth failed",)

        # Test EncodingError init (lines 203-205)
        enc_error = EncodingError("Encode failed")
        assert enc_error.error_code == GatewayErrorCode.INVALID_MESSAGE_FORMAT
        assert enc_error.args == ("Encoding error: Encode failed",)

        # Test RateLimitError init (lines 212-214)
        rate_error = RateLimitError("Rate exceeded")
        assert rate_error.error_code == HTTPErrorCode.TOO_MANY_REQUESTS
        assert rate_error.args == ("Rate limit error: Rate exceeded",)

    def test_base_protocol_error_init(self):
        """Test base OGxProtocolError initialization (lines 17-18)."""
        error = OGxProtocolError("message")
        # Test super() call was made
        assert error.args == ("message",)
        # Test error_code assignment in __init__
        assert not hasattr(error, "error_code") or error.error_code is None

    def test_protocol_error_init(self):
        """Test ProtocolError initialization (lines 25-26)."""
        error = ProtocolError("message")
        # Test super() call was made with modified message
        assert error.args == ("Protocol error: message",)
        # Test error_code assignment in __init__
        assert hasattr(error, "error_code")
        assert error.error_code == GatewayErrorCode.SUBMIT_MESSAGE_RATE_EXCEEDED

    def test_auth_error_init(self):
        """Test AuthenticationError initialization (lines 194-196)."""
        error = AuthenticationError("message")
        # Test super() call was made with modified message and default code
        assert error.args == ("Authentication error: message",)
        assert error.error_code == HTTPErrorCode.UNAUTHORIZED

    def test_encoding_error_init(self):
        """Test EncodingError initialization (lines 203-205)."""
        error = EncodingError("message")
        # Test super() call was made with modified message and default code
        assert error.args == ("Encoding error: message",)
        assert error.error_code == GatewayErrorCode.INVALID_MESSAGE_FORMAT

    def test_rate_limit_error_init(self):
        """Test RateLimitError initialization (lines 212-214)."""
        error = RateLimitError("message")
        # Test super() call was made with modified message and default code
        assert error.args == ("Rate limit error: message",)
        assert error.error_code == HTTPErrorCode.TOO_MANY_REQUESTS
