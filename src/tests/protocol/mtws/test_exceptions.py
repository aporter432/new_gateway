"""Tests for MTWS protocol exceptions.

This module contains tests that verify the protocol-specific exceptions
properly handle error conditions defined in the N206 specification.
"""

import pytest

from protocols.mtws.exceptions import (
    MTWSElementError,
    MTWSEncodingError,
    MTWSError,
    MTWSFieldError,
    MTWSSizeError,
    MTWSTransportError,
)


class TestMTWSExceptions:
    """Test suite for MTWS protocol exceptions."""

    def test_base_protocol_error(self):
        """Test base protocol error functionality."""
        error = MTWSError("Test error", 0)
        assert str(error) == "Error 0: Test error"
        assert isinstance(error, Exception)

    def test_encoding_error(self):
        """Test encoding error with error codes."""
        # Test invalid JSON format error
        error = MTWSEncodingError("Invalid JSON format", MTWSEncodingError.INVALID_JSON_FORMAT)
        assert "Invalid JSON format" in str(error)
        assert error.error_code == MTWSEncodingError.INVALID_JSON_FORMAT

        # Test encoding failed error
        error = MTWSEncodingError("Failed to encode message", MTWSEncodingError.ENCODE_FAILED)
        assert "Failed to encode message" in str(error)
        assert error.error_code == MTWSEncodingError.ENCODE_FAILED

    def test_field_error(self):
        """Test field validation error with error codes."""
        # Test invalid field name
        error = MTWSFieldError("Field name is required", MTWSFieldError.INVALID_NAME, "test_field")
        assert "Field name is required" in str(error)
        assert error.error_code == MTWSFieldError.INVALID_NAME
        assert error.field_name == "test_field"

        # Test invalid field value
        error = MTWSFieldError("Invalid field value", MTWSFieldError.INVALID_VALUE, "test_field")
        assert "Invalid field value" in str(error)
        assert error.error_code == MTWSFieldError.INVALID_VALUE
        assert error.field_name == "test_field"

    def test_element_error(self):
        """Test element validation error with error codes."""
        # Test invalid element index
        error = MTWSElementError(
            "Invalid element index", MTWSElementError.INVALID_INDEX, element_index=1
        )
        assert "Invalid element index" in str(error)
        assert error.error_code == MTWSElementError.INVALID_INDEX
        assert error.element_index == 1

        # Test missing fields
        error = MTWSElementError("Element must contain fields", MTWSElementError.MISSING_FIELDS)
        assert "Element must contain fields" in str(error)
        assert error.error_code == MTWSElementError.MISSING_FIELDS

    def test_size_error(self):
        """Test size constraint error with error codes."""
        # Test message size exceeded
        error = MTWSSizeError(
            "Message size exceeds limit",
            MTWSSizeError.EXCEEDS_MESSAGE_SIZE,
            current_size=1000,
            max_size=500,
        )
        assert "Message size exceeds limit" in str(error)
        assert error.error_code == MTWSSizeError.EXCEEDS_MESSAGE_SIZE
        assert error.current_size == 1000
        assert error.max_size == 500

    def test_transport_error(self):
        """Test transport-related error with error codes."""
        # Test connection error
        error = MTWSTransportError(
            "Failed to connect to server",
            MTWSTransportError.GPRS_UNAVAILABLE,
            transport_type="GPRS",
        )
        assert "Failed to connect to server" in str(error)
        assert error.error_code == MTWSTransportError.GPRS_UNAVAILABLE
        assert error.transport_type == "GPRS"

    def test_error_inheritance(self):
        """Test exception inheritance hierarchy."""
        # All exceptions should inherit from MTWSError
        assert issubclass(MTWSEncodingError, MTWSError)
        assert issubclass(MTWSFieldError, MTWSError)
        assert issubclass(MTWSElementError, MTWSError)
        assert issubclass(MTWSSizeError, MTWSError)
        assert issubclass(MTWSTransportError, MTWSError)

    def test_error_with_context(self):
        """Test exceptions with additional context information."""
        try:
            raise MTWSFieldError(
                "Multiple errors in field", MTWSFieldError.INVALID_VALUE, field_name="test_field"
            )
        except MTWSFieldError as e:
            assert e.field_name == "test_field"
            assert "Multiple errors in field" in str(e)
            assert e.error_code == MTWSFieldError.INVALID_VALUE

    def test_nested_exceptions(self):
        """Test handling of nested exceptions."""
        try:
            try:
                raise MTWSFieldError("Invalid field value", MTWSFieldError.INVALID_VALUE)
            except MTWSFieldError as field_error:
                raise MTWSEncodingError(
                    "Failed to encode message due to field error", MTWSEncodingError.ENCODE_FAILED
                ) from field_error
        except MTWSEncodingError as e:
            assert isinstance(e.__cause__, MTWSFieldError)
            assert "Failed to encode message due to field error" in str(e)
