"""Tests for MTBP protocol exception handling.

This module contains tests that verify the exception handling behavior
of the MTBP protocol implementation according to N210 requirements.
"""

import pytest

from protocols.mtbp.validation.exceptions import (
    MTBPError,
    ParseError,
    ValidationError,
    FormatError,
    MTBPSystemError,
    TransmissionError,
    QueueError,
    PowerError,
    RoutingError,
    SecurityError,
    ResourceError,
    ProtocolError,
)


class TestMTBPExceptions:
    """Test suite for MTBP protocol exception handling."""

    def test_parse_errors(self):
        """Test parse error conditions and error codes."""
        # Test invalid SIN
        with pytest.raises(ParseError) as exc_info:
            raise ParseError(
                message="Invalid SIN value: 256",
                error_code=ParseError.INVALID_SIN,
            )
        assert exc_info.value.error_code == ParseError.INVALID_SIN
        assert "Invalid SIN value: 256" in str(exc_info.value)

        # Test invalid MIN
        with pytest.raises(ParseError) as exc_info:
            raise ParseError(
                message="Invalid MIN value: 256",
                error_code=ParseError.INVALID_MIN,
            )
        assert exc_info.value.error_code == ParseError.INVALID_MIN
        assert "Invalid MIN value: 256" in str(exc_info.value)

        # Test invalid message type
        with pytest.raises(ParseError) as exc_info:
            raise ParseError(
                message="Invalid message type: INVALID",
                error_code=ParseError.INVALID_FIELD_TYPE,
            )
        assert exc_info.value.error_code == ParseError.INVALID_FIELD_TYPE
        assert "Invalid message type" in str(exc_info.value)

    def test_protocol_errors(self):
        """Test protocol error conditions and error codes."""
        # Test invalid sequence number
        with pytest.raises(ProtocolError) as exc_info:
            raise ProtocolError(
                message="Invalid sequence number - out of valid range",
                error_code=ProtocolError.SEQUENCE_ERROR,
            )
        assert exc_info.value.error_code == ProtocolError.SEQUENCE_ERROR

        # Test protocol timeout
        with pytest.raises(ProtocolError) as exc_info:
            raise ProtocolError(
                message="Protocol operation timed out",
                error_code=ProtocolError.PROTOCOL_TIMEOUT,
            )
        assert exc_info.value.error_code == ProtocolError.PROTOCOL_TIMEOUT

    def test_validation_errors(self):
        """Test validation error conditions and error codes."""
        # Test missing required field
        with pytest.raises(ValidationError) as exc_info:
            raise ValidationError(
                message="Missing required fields in message",
                error_code=ValidationError.INVALID_INPUT_DATA,
            )
        assert exc_info.value.error_code == ValidationError.INVALID_INPUT_DATA
        assert "Missing required fields" in str(exc_info.value)

        # Test invalid field combination
        with pytest.raises(ValidationError) as exc_info:
            raise ValidationError(
                message="Invalid field combination - duplicate field types not allowed",
                error_code=ValidationError.INVALID_INPUT_DATA,
            )
        assert exc_info.value.error_code == ValidationError.INVALID_INPUT_DATA
        assert "Invalid field combination" in str(exc_info.value)

    def test_field_errors(self):
        """Test field-specific error conditions and error codes."""
        # Test invalid field type
        with pytest.raises(ParseError) as exc_info:
            raise ParseError(
                message="Invalid field type: INVALID",
                error_code=ParseError.INVALID_FIELD_TYPE,
            )
        assert exc_info.value.error_code == ParseError.INVALID_FIELD_TYPE
        assert "Invalid field type" in str(exc_info.value)

        # Test invalid field value type
        with pytest.raises(ParseError) as exc_info:
            raise ParseError(
                message="Invalid field value type: expected int, got str",
                error_code=ParseError.INVALID_FIELD_VALUE,
            )
        assert exc_info.value.error_code == ParseError.INVALID_FIELD_VALUE
        assert "Invalid field value type" in str(exc_info.value)

        # Test field value out of range
        with pytest.raises(ParseError) as exc_info:
            raise ParseError(
                message="Field value out of range: -1 for unsigned int",
                error_code=ParseError.INVALID_FIELD_VALUE,
            )
        assert exc_info.value.error_code == ParseError.INVALID_FIELD_VALUE
        assert "Field value out of range" in str(exc_info.value)

    def test_error_inheritance(self):
        """Test error class inheritance and type checking."""
        # Create sample errors
        parse_error = ParseError("Invalid SIN value", error_code=ParseError.INVALID_SIN)
        protocol_error = ProtocolError(
            "Invalid sequence number", error_code=ProtocolError.SEQUENCE_ERROR
        )
        validation_error = ValidationError(
            "Invalid timestamp format", error_code=ValidationError.INVALID_TIMESTAMP_FORMAT
        )

        # Test that all errors inherit from MTBPError
        assert isinstance(parse_error, ParseError)
        assert isinstance(protocol_error, ProtocolError)
        assert isinstance(validation_error, ValidationError)

        # Test error code uniqueness
        error_codes = set()
        for error in [parse_error, protocol_error, validation_error]:
            assert error.error_code not in error_codes
            error_codes.add(error.error_code)

    def test_error_messages(self):
        """Test error message formatting and content."""
        # Test basic error message
        error = ValidationError(
            message="Missing required field 'test_field'",
            error_code=ValidationError.INVALID_INPUT_DATA,
        )
        assert "Missing required field 'test_field'" in str(error)

        # Test error with context
        error = ParseError(
            message="Invalid message format",
            error_code=ParseError.INVALID_FORMAT,
        )
        error_str = str(error)
        assert "Invalid message format" in error_str


def test_base_exception():
    """Test base MTBPError functionality."""
    # Test with error code
    error = MTBPError("Test error", error_code=123)
    assert str(error) == "Test error"
    assert error.error_code == 123

    # Test without error code
    error = MTBPError("Test error")
    assert str(error) == "Test error"
    assert error.error_code is None


def test_parse_error():
    """Test ParseError error codes and messages."""
    # Test all defined error codes
    test_cases = [
        (ParseError.INVALID_FORMAT, "Invalid format"),
        (ParseError.INVALID_SIN, "Invalid SIN"),
        (ParseError.INVALID_MIN, "Invalid MIN"),
        (ParseError.INVALID_FIELD_TYPE, "Invalid field type"),
        (ParseError.INVALID_FIELD_VALUE, "Invalid field value"),
        (ParseError.MISSING_FIELD, "Missing field"),
        (ParseError.INVALID_SIZE, "Invalid size"),
        (ParseError.INVALID_CHECKSUM, "Invalid checksum"),
        (ParseError.UNSUPPORTED_VERSION, "Unsupported version"),
        (ParseError.DECODE_FAILED, "Decode failed"),
        (ParseError.INVALID_STRUCTURE, "Invalid structure"),
        (ParseError.VALIDATION_FAILED, "Validation failed"),
        (ParseError.INVALID_SEQUENCE, "Invalid sequence"),
    ]

    for error_code, message in test_cases:
        error = ParseError(message, error_code=error_code)
        assert isinstance(error, MTBPError)
        assert error.error_code == error_code
        assert str(error) == message


def test_validation_error():
    """Test ValidationError error codes and messages."""
    test_cases = [
        (ValidationError.INVALID_TIMESTAMP_FORMAT, "Invalid timestamp"),
        (ValidationError.INVALID_INPUT_DATA, "Invalid input"),
        (ValidationError.INVALID_TERMINAL_ID, "Invalid terminal ID"),
        (ValidationError.INVALID_MESSAGE_PRIORITY, "Invalid priority"),
        (ValidationError.INVALID_DESTINATION_ID, "Invalid destination"),
        (ValidationError.INVALID_SOURCE_ID, "Invalid source"),
    ]

    for error_code, message in test_cases:
        error = ValidationError(message, error_code=error_code)
        assert isinstance(error, MTBPError)
        assert error.error_code == error_code
        assert str(error) == message


def test_format_error():
    """Test FormatError error codes and messages."""
    test_cases = [
        (FormatError.INVALID_MESSAGE_FORMAT, "Invalid message format"),
        (FormatError.INVALID_MESSAGE_CONTENT, "Invalid content"),
        (FormatError.MESSAGE_TOO_LARGE, "Message too large"),
        (FormatError.INVALID_MESSAGE_TYPE, "Invalid message type"),
    ]

    for error_code, message in test_cases:
        error = FormatError(message, error_code=error_code)
        assert isinstance(error, MTBPError)
        assert error.error_code == error_code
        assert str(error) == message


def test_system_error():
    """Test MTBPSystemError error codes and messages."""
    test_cases = [
        (MTBPSystemError.INTERNAL_ERROR, "Internal error"),
        (MTBPSystemError.DATABASE_ERROR, "Database error"),
        (MTBPSystemError.NETWORK_ERROR, "Network error"),
        (MTBPSystemError.SERVICE_UNAVAILABLE, "Service unavailable"),
    ]

    for error_code, message in test_cases:
        error = MTBPSystemError(message, error_code=error_code)
        assert isinstance(error, MTBPError)
        assert error.error_code == error_code
        assert str(error) == message


def test_transmission_error():
    """Test TransmissionError error codes and messages."""
    test_cases = [
        (TransmissionError.TRANSMISSION_FAILED, "Transmission failed"),
        (TransmissionError.NETWORK_CONGESTION, "Network congestion"),
        (TransmissionError.SIGNAL_LOST, "Signal lost"),
        (TransmissionError.TERMINAL_UNREACHABLE, "Terminal unreachable"),
        (TransmissionError.TRANSPORT_UNAVAILABLE, "Transport unavailable"),
        (TransmissionError.BANDWIDTH_EXCEEDED, "Bandwidth exceeded"),
        (TransmissionError.TERMINAL_BUSY, "Terminal busy"),
    ]

    for error_code, message in test_cases:
        error = TransmissionError(message, error_code=error_code)
        assert isinstance(error, MTBPError)
        assert error.error_code == error_code
        assert str(error) == message


def test_queue_error():
    """Test QueueError error codes and messages."""
    test_cases = [
        (QueueError.QUEUE_FULL, "Queue full"),
        (QueueError.PRIORITY_INVALID, "Invalid priority"),
        (QueueError.QUEUE_DISABLED, "Queue disabled"),
        (QueueError.MESSAGE_EXPIRED, "Message expired"),
        (QueueError.DUPLICATE_MESSAGE, "Duplicate message"),
        (QueueError.QUEUE_SUSPENDED, "Queue suspended"),
    ]

    for error_code, message in test_cases:
        error = QueueError(message, error_code=error_code)
        assert isinstance(error, MTBPError)
        assert error.error_code == error_code
        assert str(error) == message


def test_power_error():
    """Test PowerError error codes and messages."""
    test_cases = [
        (PowerError.LOW_BATTERY, "Low battery"),
        (PowerError.POWER_MODE_INVALID, "Invalid power mode"),
        (PowerError.WAKE_SCHEDULE_ERROR, "Wake schedule error"),
        (PowerError.POWER_SAVING_ACTIVE, "Power saving active"),
        (PowerError.CHARGING_REQUIRED, "Charging required"),
    ]

    for error_code, message in test_cases:
        error = PowerError(message, error_code=error_code)
        assert isinstance(error, MTBPError)
        assert error.error_code == error_code
        assert str(error) == message


def test_routing_error():
    """Test RoutingError error codes and messages."""
    test_cases = [
        (RoutingError.NO_ROUTE_AVAILABLE, "No route available"),
        (RoutingError.ROUTE_EXPIRED, "Route expired"),
        (RoutingError.DELIVERY_FAILED, "Delivery failed"),
        (RoutingError.ROUTE_INVALID, "Invalid route"),
        (RoutingError.TRANSPORT_MISMATCH, "Transport mismatch"),
        (RoutingError.ROUTING_DISABLED, "Routing disabled"),
    ]

    for error_code, message in test_cases:
        error = RoutingError(message, error_code=error_code)
        assert isinstance(error, MTBPError)
        assert error.error_code == error_code
        assert str(error) == message


def test_security_error():
    """Test SecurityError error codes and messages."""
    test_cases = [
        (SecurityError.AUTHENTICATION_FAILED, "Authentication failed"),
        (SecurityError.UNAUTHORIZED_ACCESS, "Unauthorized access"),
        (SecurityError.ENCRYPTION_FAILED, "Encryption failed"),
        (SecurityError.CERTIFICATE_INVALID, "Invalid certificate"),
        (SecurityError.KEY_EXPIRED, "Key expired"),
        (SecurityError.SECURITY_VIOLATION, "Security violation"),
    ]

    for error_code, message in test_cases:
        error = SecurityError(message, error_code=error_code)
        assert isinstance(error, MTBPError)
        assert error.error_code == error_code
        assert str(error) == message


def test_resource_error():
    """Test ResourceError error codes and messages."""
    test_cases = [
        (ResourceError.MEMORY_FULL, "Memory full"),
        (ResourceError.CPU_OVERLOAD, "CPU overload"),
        (ResourceError.RESOURCE_UNAVAILABLE, "Resource unavailable"),
        (ResourceError.STORAGE_FULL, "Storage full"),
        (ResourceError.RESOURCE_TIMEOUT, "Resource timeout"),
        (ResourceError.RESOURCE_LOCKED, "Resource locked"),
    ]

    for error_code, message in test_cases:
        error = ResourceError(message, error_code=error_code)
        assert isinstance(error, MTBPError)
        assert error.error_code == error_code
        assert str(error) == message


def test_protocol_error():
    """Test ProtocolError error codes and messages."""
    test_cases = [
        (ProtocolError.VERSION_MISMATCH, "Version mismatch"),
        (ProtocolError.SEQUENCE_ERROR, "Sequence error"),
        (ProtocolError.HANDSHAKE_FAILED, "Handshake failed"),
        (ProtocolError.PROTOCOL_TIMEOUT, "Protocol timeout"),
        (ProtocolError.SYNC_ERROR, "Sync error"),
        (ProtocolError.PROTOCOL_VIOLATION, "Protocol violation"),
    ]

    for error_code, message in test_cases:
        error = ProtocolError(message, error_code=error_code)
        assert isinstance(error, MTBPError)
        assert error.error_code == error_code
        assert str(error) == message


def test_error_code_uniqueness():
    """Test that all error codes are unique across all error classes."""
    error_codes = set()
    error_classes = [
        ParseError,
        ValidationError,
        FormatError,
        MTBPSystemError,
        TransmissionError,
        QueueError,
        PowerError,
        RoutingError,
        SecurityError,
        ResourceError,
        ProtocolError,
    ]

    for error_class in error_classes:
        for name, value in vars(error_class).items():
            if isinstance(value, int) and not name.startswith("_"):
                assert value not in error_codes, f"Duplicate error code {value} found"
                error_codes.add(value)


def test_error_inheritance():
    """Test that all error classes properly inherit from MTBPError."""
    error_classes = [
        ParseError,
        ValidationError,
        FormatError,
        MTBPSystemError,
        TransmissionError,
        QueueError,
        PowerError,
        RoutingError,
        SecurityError,
        ResourceError,
        ProtocolError,
    ]

    for error_class in error_classes:
        # Test inheritance
        assert issubclass(error_class, MTBPError)
        assert issubclass(error_class, Exception)

        # Test instance creation
        error = error_class("Test message", error_code=1)
        assert isinstance(error, error_class)
        assert isinstance(error, MTBPError)
        assert isinstance(error, Exception)
