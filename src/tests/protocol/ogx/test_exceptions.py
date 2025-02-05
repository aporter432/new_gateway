"""Tests for OGx protocol exceptions"""

import pytest

from src.protocols.ogx.exceptions import (
    OGxProtocolError,
    ProtocolError,
    MessageFormatError,
    FieldFormatError,
    ElementFormatError,
    ValidationError,
    EncodingError,
)


@pytest.fixture
def test_error_msg():
    """Fixture providing a test error message"""
    return "Test error message"


class TestOGxProtocolError:
    """Test cases for the base OGx protocol error class"""

    def test_base_exception(self, test_error_msg):
        """Test base exception with error code"""
        error = OGxProtocolError(test_error_msg, 1001)
        assert str(error) == test_error_msg
        assert error.error_code == 1001

    def test_base_exception_no_code(self):
        """Test base exception without error code"""
        error = OGxProtocolError("Test error")
        assert str(error) == "Test error"
        assert error.error_code is None


class TestProtocolError:
    """Test cases for protocol-specific errors"""

    def test_protocol_error_with_code(self):
        """Test protocol error with specific error code"""
        error = ProtocolError("Rate exceeded", ProtocolError.ERR_SUBMIT_MESSAGE_RATE_EXCEEDED)
        assert str(error) == "Protocol error: Rate exceeded"
        assert error.error_code == ProtocolError.ERR_SUBMIT_MESSAGE_RATE_EXCEEDED

    def test_protocol_error_constants(self):
        """Test protocol error constant values"""
        assert ProtocolError.ERR_SUBMIT_MESSAGE_RATE_EXCEEDED == 24579
        assert ProtocolError.ERR_RETRIEVE_STATUS_RATE_EXCEEDED == 24581
        assert ProtocolError.ERR_NDN_INVALID_BEAM == 12308


class TestMessageFormatError:
    """Test cases for message format errors"""

    def test_message_format_error(self):
        """Test message format error without error code"""
        error = MessageFormatError("Invalid message structure")
        assert str(error) == "Message format error: Invalid message structure"
        assert error.error_code is None

    def test_message_format_error_with_code(self):
        """Test message format error with error code"""
        error = MessageFormatError("Invalid message structure", 1001)
        assert str(error) == "Message format error: Invalid message structure"
        assert error.error_code == 1001


class TestFieldFormatError:
    """Test cases for field format errors"""

    def test_field_format_error(self):
        """Test field format error without error code"""
        error = FieldFormatError("Invalid field type")
        assert str(error) == "Field format error: Invalid field type"
        assert error.error_code is None

    def test_field_format_error_with_code(self):
        """Test field format error with error code"""
        error = FieldFormatError("Invalid field type", 1002)
        assert str(error) == "Field format error: Invalid field type"
        assert error.error_code == 1002


class TestElementFormatError:
    """Test cases for element format errors"""

    def test_element_format_error(self):
        """Test element format error without error code"""
        error = ElementFormatError("Invalid element index")
        assert str(error) == "Element format error: Invalid element index"
        assert error.error_code is None

    def test_element_format_error_with_code(self):
        """Test element format error with error code"""
        error = ElementFormatError("Invalid element index", 1005)
        assert str(error) == "Element format error: Invalid element index"
        assert error.error_code == 1005


class TestValidationError:
    """Test cases for validation errors"""

    def test_validation_error_constants(self):
        """Test validation error constant values"""
        assert ValidationError.MISSING_REQUIRED_FIELD == 1001
        assert ValidationError.INVALID_FIELD_TYPE == 1002
        assert ValidationError.INVALID_FIELD_VALUE == 1003
        assert ValidationError.DUPLICATE_FIELD_NAME == 1004
        assert ValidationError.INVALID_ELEMENT_INDEX == 1005
        assert ValidationError.FIELD_VALUE_AND_ELEMENTS == 1006
        assert ValidationError.INVALID_MESSAGE_FORMAT == 1007
        assert ValidationError.INVALID_FIELD_FORMAT == 1008
        assert ValidationError.INVALID_ELEMENT_FORMAT == 1009

    def test_validation_error_with_code(self):
        """Test validation error with error code"""
        error = ValidationError("Missing required field", ValidationError.MISSING_REQUIRED_FIELD)
        assert str(error) == "Validation error: Missing required field"
        assert error.error_code == ValidationError.MISSING_REQUIRED_FIELD


class TestEncodingError:
    """Test cases for encoding errors"""

    def test_encoding_error(self):
        """Test encoding error without error code"""
        error = EncodingError("Failed to encode message")
        assert str(error) == "Encoding error: Failed to encode message"
        assert error.error_code is None

    def test_encoding_error_with_code(self):
        """Test encoding error with error code"""
        error = EncodingError("Failed to encode message", 2001)
        assert str(error) == "Encoding error: Failed to encode message"
        assert error.error_code == 2001
