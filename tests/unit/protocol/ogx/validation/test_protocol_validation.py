"""Tests for protocol-level validators."""

import pytest

from protocols.ogx.validation.protocol.network_validator import NetworkValidator
from protocols.ogx.validation.protocol.size_validator import SizeValidator
from protocols.ogx.validation.protocol.transport_validator import TransportValidator
from protocols.ogx.validation.common.types import ValidationContext, MessageType, ValidationResult
from protocols.ogx.validation.common.validation_exceptions import (
    ValidationError,
    SizeValidationError,  # Added missing import
)
from protocols.ogx.constants.network_types import NetworkType


class TestNetworkValidator:
    """Test network validation."""

    @pytest.fixture
    def validator(self):
        return NetworkValidator()

    @pytest.fixture
    def context(self):
        return ValidationContext(network_type="OGx", direction=MessageType.FORWARD)

    def test_validate_valid_network(self, validator, context):
        """Test validation with valid network type."""
        result = validator.validate({"network": "OGx"}, context)
        assert result.is_valid

    def test_validate_invalid_network(self, validator, context):
        """Test validation with invalid network type."""
        result = validator.validate({"network": "Invalid"}, context)
        assert not result.is_valid
        assert "Invalid network type" in result.errors[0]

    def test_validate_missing_network(self, validator, context):
        """Test validation with missing network."""
        result = validator.validate({}, context)
        assert not result.is_valid
        assert "Missing network type" in result.errors[0]

    def test_validate_with_invalid_data_type(self, validator, context):
        """Test validation with non-dict input."""
        result = validator.validate("not a dict", context)
        assert not result.is_valid
        assert "Invalid data type" in result.errors[0]

    def test_validate_with_missing_network(self, validator, context):
        """Test validation with missing network field."""
        result = validator.validate({}, context)
        assert not result.is_valid
        assert "Missing network type" in result.errors[0]

    def test_validate_with_invalid_network(self, validator, context):
        """Test validation with invalid network value."""
        result = validator.validate({"network": "invalid"}, context)
        assert not result.is_valid
        assert "Invalid network type" in result.errors[0]

    def test_validate_with_valid_network(self, validator, context):
        """Test validation with valid network value."""
        result = validator.validate({"network": "OGx"}, context)
        assert result.is_valid

    def test_validate_none_input(self, validator, context):
        """Test validation with None input."""
        result = validator.validate(None, context)
        assert not result.is_valid
        assert "Invalid data" in result.errors[0]

    def test_validate_wrong_network_type(self, validator, context):
        """Test validation with wrong network type in context."""
        context = ValidationContext(network_type="INVALID", direction=MessageType.FORWARD)
        result = validator.validate({"network": "OGx"}, context)
        assert not result.is_valid
        assert "Invalid network type in context" in result.errors[0]


class TestSizeValidator:
    """Test size validation."""

    @pytest.fixture
    def validator(self):
        """Create validator with 1000 byte limit."""
        return SizeValidator(message_size_limit=1000)  # Fixed parameter name

    @pytest.fixture
    def context(self):
        return ValidationContext(network_type="OGx", direction=MessageType.FORWARD)

    def test_validate_valid_size(self, validator, context):
        """Test validation with valid message size."""
        data = {"payload": "x" * 500}  # Message under size limit
        result = validator.validate(data, context)
        assert result.is_valid

    def test_validate_oversized(self, validator, context):
        """Test validation with oversized message."""
        data = {"payload": "x" * 1500}  # Message over size limit
        result = validator.validate(data, context)
        assert not result.is_valid
        assert "exceeds maximum size" in result.errors[0]

    def test_validate_edge_case(self, validator, context):
        """Test validation at size limit boundary."""
        data = {"payload": "x" * 1000}  # Message at size limit
        result = validator.validate(data, context)
        assert result.is_valid

    def test_validate_with_no_data(self, validator, context):
        """Test validation with no data."""
        result = validator.validate(None, context)
        assert not result.is_valid
        assert "No data to validate" in result.errors[0]

    def test_validate_with_empty_data(self, validator, context):
        """Test validation with empty data."""
        result = validator.validate({}, context)
        assert not result.is_valid
        assert "No data to validate" in result.errors[0]

    def test_validate_with_valid_size(self, validator, context):
        """Test validation with valid message size."""
        result = validator.validate({"payload": "x" * 500}, context)
        assert result.is_valid

    def test_validate_with_oversized_data(self, validator, context):
        """Test validation with oversized message."""
        with pytest.raises(SizeValidationError) as exc:
            validator.validate({"payload": "x" * 1500}, context)
        assert "exceeds maximum size" in str(exc.value)
        assert exc.value.current_size == len(str({"payload": "x" * 1500}))
        assert exc.value.max_size == 1000

    def test_validate_empty_message(self, validator, context):
        """Test validation with empty message."""
        data = {"payload": ""}
        result = validator.validate(data, context)
        assert result.is_valid

    def test_validate_complex_message(self, validator, context):
        """Test validation with complex nested message."""
        data = {
            "header": {"version": "1.0"},
            "payload": "x" * 500,
            "metadata": {"timestamp": "2023-01-01"},
        }
        result = validator.validate(data, context)
        assert result.is_valid


class TestTransportValidator:
    """Test transport validation."""

    @pytest.fixture
    def validator(self):
        return TransportValidator()

    @pytest.fixture
    def context(self):
        return ValidationContext(network_type="OGx", direction=MessageType.FORWARD)

    def test_validate_valid_transport(self, validator, context):
        """Test validation with valid transport type."""
        result = validator.validate({"transport": "satellite"}, context)
        assert result.is_valid

    def test_validate_invalid_transport(self, validator, context):
        """Test validation with invalid transport type."""
        result = validator.validate({"transport": "invalid"}, context)
        assert not result.is_valid
        assert "Invalid transport type" in result.errors[0]

    def test_validate_missing_transport(self, validator, context):
        """Test validation with missing transport."""
        result = validator.validate({}, context)
        assert not result.is_valid
        assert "Missing transport type" in result.errors[0]

    def test_validate_cellular_transport(self, validator, context):
        """Test validation with cellular transport."""
        result = validator.validate({"transport": "cellular"}, context)
        assert result.is_valid

    def test_validate_with_both_transports(self, validator, context):
        """Test validation when both transports are specified."""
        result = validator.validate({"transport": ["satellite", "cellular"]}, context)
        assert result.is_valid

    def test_validate_with_no_transport(self, validator, context):
        """Test validation with missing transport field."""
        result = validator.validate({}, context)
        assert not result.is_valid
        assert "Missing transport type" in result.errors[0]

    def test_validate_with_invalid_transport(self, validator, context):
        """Test validation with invalid transport value."""
        result = validator.validate({"transport": "invalid"}, context)
        assert not result.is_valid
        assert "Invalid transport type" in result.errors[0]

    def test_validate_with_valid_transport(self, validator, context):
        """Test validation with valid transport values."""
        # Test satellite
        result = validator.validate({"transport": "satellite"}, context)
        assert result.is_valid

        # Test cellular
        result = validator.validate({"transport": "cellular"}, context)
        assert result.is_valid

        # Test array of transports
        result = validator.validate({"transport": ["satellite", "cellular"]}, context)
        assert result.is_valid

    def test_validate_transport_case_insensitive(self, validator, context):
        """Test validation is case insensitive."""
        result = validator.validate({"transport": "SATELLITE"}, context)
        assert result.is_valid

        result = validator.validate({"transport": "Cellular"}, context)
        assert result.is_valid

    def test_validate_transport_mixed_array(self, validator, context):
        """Test validation with mixed case array."""
        result = validator.validate({"transport": ["SATELLITE", "cellular", "Satellite"]}, context)
        assert result.is_valid
