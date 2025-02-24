"""Test OGx protocol exceptions and error handling.

Tests the error codes and exception handling for the OGx protocol
as defined in OGx-1.txt.
"""

import pytest

from Protexis_Command.api_ogx.config.http_error_codes import HTTPErrorCode
from Protexis_Command.protocol.ogx.constants.ogx_error_codes import GatewayErrorCode
from Protexis_Command.protocol.ogx.validation.ogx_validation_exceptions import (
    EncodingError,
    OGxProtocolError,
    ProtocolError,
    ValidationError,
)


@pytest.fixture
def test_error_msg():
    """Fixture providing a test error message."""
    return "Test error message"


class TestOGxProtocolError:
    """Test cases for the base OGx protocol error class."""

    def test_base_exception(self, test_error_msg):
        """Test base exception with error code."""
        error = OGxProtocolError(test_error_msg, GatewayErrorCode.VALIDATION_ERROR)
        assert str(error) == test_error_msg
        assert error.error_code == GatewayErrorCode.VALIDATION_ERROR

    def test_base_exception_no_code(self):
        """Test base exception without error code."""
        error = OGxProtocolError("Test error")
        assert str(error) == "Test error"
        assert error.error_code is None


class TestProtocolError:
    """Test cases for protocol-specific errors."""

    def test_protocol_error_with_code(self):
        """Test protocol error with specific error code."""
        error = ProtocolError("Rate exceeded", GatewayErrorCode.SUBMIT_MESSAGE_RATE_EXCEEDED)
        assert str(error) == "Protocol error: Rate exceeded"
        assert error.error_code == GatewayErrorCode.SUBMIT_MESSAGE_RATE_EXCEEDED

    def test_protocol_error_constants(self):
        """Test protocol error constant values from OGx-1.txt."""
        # Rate limiting errors (24500-24599)
        assert GatewayErrorCode.SUBMIT_MESSAGE_RATE_EXCEEDED == 24579
        assert GatewayErrorCode.RETRIEVE_STATUS_RATE_EXCEEDED == 24581
        assert GatewayErrorCode.INVALID_TOKEN == 24582
        assert GatewayErrorCode.TOKEN_EXPIRED == 24583
        assert GatewayErrorCode.TOKEN_REVOKED == 24584
        assert GatewayErrorCode.TOKEN_INVALID_FORMAT == 24585


class TestValidationError:
    """Test cases for validation errors."""

    def test_validation_error_with_code(self):
        """Test validation error with error code."""
        error = ValidationError("Invalid message format", GatewayErrorCode.INVALID_MESSAGE_FORMAT)
        assert str(error) == "Validation error: Invalid message format"
        assert error.error_code == GatewayErrorCode.INVALID_MESSAGE_FORMAT

    def test_validation_error_with_details(self):
        """Test validation error with additional details."""
        error = ValidationError(
            "Invalid message format",
            GatewayErrorCode.INVALID_MESSAGE_FORMAT,
            details={"field": "temperature", "value": "invalid"},
        )
        expected_msg = "Validation error: Invalid message format (field=temperature, value=invalid)"
        assert str(error) == expected_msg
        assert error.error_code == GatewayErrorCode.INVALID_MESSAGE_FORMAT

    def test_validation_error_constants(self):
        """Test validation error constant values from OGx-1.txt."""
        # Base validation errors (10000-10099)
        assert GatewayErrorCode.VALIDATION_ERROR == 10000
        assert GatewayErrorCode.INVALID_MESSAGE_FORMAT == 10001
        assert GatewayErrorCode.INVALID_ELEMENT_FORMAT == 10002
        assert GatewayErrorCode.INVALID_FIELD_FORMAT == 10003
        assert GatewayErrorCode.INVALID_MESSAGE_FILTER == 10004
        assert GatewayErrorCode.MESSAGE_SIZE_EXCEEDED == 10005
        assert GatewayErrorCode.INVALID_FIELD_TYPE == 10006


class TestEncodingError:
    """Test cases for encoding errors."""

    def test_encoding_error(self):
        """Test encoding error defaults to ENCODE_ERROR code."""
        error = EncodingError("Failed to encode message")
        assert str(error) == "Encoding error: Failed to encode message"
        assert error.error_code == GatewayErrorCode.ENCODE_ERROR

    def test_encoding_error_with_code(self):
        """Test encoding error with explicit error code."""
        error = EncodingError("Failed to encode message", GatewayErrorCode.ENCODE_ERROR)
        assert str(error) == "Encoding error: Failed to encode message"
        assert error.error_code == GatewayErrorCode.ENCODE_ERROR

    def test_encoding_error_code_range(self):
        """Test encoding error code is in correct range per OGx-1.txt."""
        # Processing errors (26000-26099)
        assert 26000 <= GatewayErrorCode.ENCODE_ERROR <= 26099


class TestHTTPErrors:
    """Test HTTP error codes as defined in OGx-1.txt Appendix A."""

    def test_http_error_codes(self):
        """Verify HTTP error codes match OGx-1.txt Appendix A."""
        assert HTTPErrorCode.SUCCESS == 200
        assert HTTPErrorCode.UNAUTHORIZED == 401
        assert HTTPErrorCode.FORBIDDEN == 403
        assert HTTPErrorCode.TOO_MANY_REQUESTS == 429
        assert HTTPErrorCode.SERVICE_UNAVAILABLE == 503


class TestGatewayErrors:
    """Test gateway error codes as defined in OGx-1.txt."""

    def test_validation_errors(self):
        """Test validation error codes (10000-10099)."""
        assert GatewayErrorCode.VALIDATION_ERROR == 10000
        assert GatewayErrorCode.INVALID_MESSAGE_FORMAT == 10001
        assert GatewayErrorCode.INVALID_ELEMENT_FORMAT == 10002
        assert GatewayErrorCode.INVALID_FIELD_FORMAT == 10003
        assert GatewayErrorCode.INVALID_MESSAGE_FILTER == 10004
        assert GatewayErrorCode.MESSAGE_SIZE_EXCEEDED == 10005
        assert GatewayErrorCode.INVALID_FIELD_TYPE == 10006

    def test_rate_limit_errors(self):
        """Test rate limiting error codes (24500-24599)."""
        assert GatewayErrorCode.SUBMIT_MESSAGE_RATE_EXCEEDED == 24579
        assert GatewayErrorCode.RETRIEVE_STATUS_RATE_EXCEEDED == 24581
        assert GatewayErrorCode.INVALID_TOKEN == 24582
        assert GatewayErrorCode.TOKEN_EXPIRED == 24583
        assert GatewayErrorCode.TOKEN_REVOKED == 24584
        assert GatewayErrorCode.TOKEN_INVALID_FORMAT == 24585

    def test_processing_errors(self):
        """Test processing error codes (26000-26099)."""
        assert GatewayErrorCode.ENCODE_ERROR == 26000
        assert GatewayErrorCode.DECODE_ERROR == 26001
        assert GatewayErrorCode.PROCESSING_ERROR == 26002
        assert GatewayErrorCode.INTERNAL_ERROR == 26003

    def test_success_code(self):
        """Test success code is 0."""
        assert GatewayErrorCode.SUCCESS == 0


class TestExceptions:
    """Test OGx protocol exceptions."""

    def test_validation_error(self):
        """Test ValidationError exception."""
        with pytest.raises(ValidationError) as exc:
            raise ValidationError("Test validation error")
        assert exc.value.error_code == GatewayErrorCode.VALIDATION_ERROR
        assert str(exc.value).startswith("Validation error:")

    def test_protocol_error(self):
        """Test ProtocolError exception."""
        with pytest.raises(ProtocolError) as exc:
            raise ProtocolError("Test protocol error", GatewayErrorCode.PROCESSING_ERROR)
        assert exc.value.error_code == GatewayErrorCode.PROCESSING_ERROR

    def test_ogx_protocol_error(self):
        """Test OGxProtocolError exception."""
        with pytest.raises(OGxProtocolError) as exc:
            raise OGxProtocolError("Test OGx error", GatewayErrorCode.ENCODE_ERROR)
        assert exc.value.error_code == GatewayErrorCode.ENCODE_ERROR
