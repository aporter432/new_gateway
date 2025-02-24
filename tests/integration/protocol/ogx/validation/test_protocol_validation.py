"""Integration tests for OGx protocol validation.

This module tests the OGx protocol validation functionality.
"""

import pytest

from Protexis_Command.protocol.ogx.constants import MessageType, NetworkType
from Protexis_Command.protocol.ogx.constants.ogx_limits import MAX_OGX_PAYLOAD_BYTES
from Protexis_Command.protocol.ogx.validation.validators.ogx_network_validator import (
    NetworkValidator,
)
from Protexis_Command.protocol.ogx.validation.validators.ogx_size_validator import SizeValidator
from Protexis_Command.protocol.ogx.validation.validators.ogx_transport_validator import (
    OGxTransportValidator,
)
from Protexis_Command.protocol.ogx.validation.validators.ogx_type_validator import ValidationContext


class TestNetworkValidator:
    """Test network validation."""

    @pytest.fixture
    def validator(self) -> NetworkValidator:
        """Return a network validator instance."""
        return NetworkValidator()

    @pytest.fixture
    def context(self) -> ValidationContext:
        """Return a validation context."""
        return ValidationContext(network_type=NetworkType.OGX, direction=MessageType.FORWARD)

    def test_validate_valid_network(self, validator: NetworkValidator, context: ValidationContext):
        """Test validation with valid network type."""
        result = validator.validate({"network": NetworkType.OGX}, context)
        assert result.is_valid

    def test_validate_invalid_network(self, validator, context):
        """Test validation with invalid network type."""
        result = validator.validate({"network": NetworkType.ISATDATA_PRO}, context)
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
        result = validator.validate({"network": NetworkType.ISATDATA_PRO}, context)
        assert not result.is_valid
        assert "Invalid network type" in result.errors[0]

    def test_validate_with_valid_network(self, validator, context):
        """Test validation with valid network value."""
        result = validator.validate({"network": NetworkType.OGX}, context)
        assert result.is_valid

    def test_validate_none_input(self, validator, context):
        """Test validation with None input."""
        result = validator.validate(None, context)
        assert not result.is_valid
        assert "Invalid data" in result.errors[0]

    def test_validate_wrong_network_type(self, validator, context):
        """Test validation with wrong network type in context."""
        context = ValidationContext(
            network_type=NetworkType.ISATDATA_PRO, direction=MessageType.FORWARD
        )
        result = validator.validate({"network": NetworkType.OGX}, context)
        assert not result.is_valid
        assert "Invalid network type in context" in result.errors[0]

    def test_validate_with_none_context(self, validator):
        """Test validation with None context."""
        result = validator.validate({"network": NetworkType.OGX}, None)
        assert not result.is_valid
        assert "Missing message direction" in result.errors[0]

    def test_validate_with_none_context_direction(self, validator: NetworkValidator):
        """Test validation with None context direction."""
        # Create context with valid direction first, then modify for test
        context = ValidationContext(network_type=NetworkType.OGX, direction=MessageType.FORWARD)
        context.direction = None  # type: ignore  # Intentionally setting invalid type for test
        result = validator.validate({"network": NetworkType.OGX}, context)
        assert not result.is_valid
        assert "Missing message direction" in result.errors[0]

    def test_validate_with_none_context_network_type(self, validator: NetworkValidator):
        """Test validation with None context network type."""
        # Create context with valid network_type first, then modify for test
        context = ValidationContext(network_type=NetworkType.OGX, direction=MessageType.FORWARD)
        context.network_type = None  # type: ignore  # Intentionally setting invalid type for test
        result = validator.validate({"network": NetworkType.OGX}, context)
        assert not result.is_valid
        assert "Missing network type in context" in result.errors[0]

    def test_validate_with_invalid_direction(self, validator: NetworkValidator):
        """Test validation with invalid message direction."""
        # Create context with valid direction first, then modify for test
        context = ValidationContext(network_type=NetworkType.OGX, direction=MessageType.FORWARD)
        context.direction = "INVALID"  # type: ignore  # Intentionally setting invalid type for test
        result = validator.validate({"network": NetworkType.OGX}, context)
        assert not result.is_valid
        assert "Invalid message direction" in result.errors[0]


class TestSizeValidator:
    """Test size validation according to OGx-1.txt."""

    @pytest.fixture
    def validator(self) -> SizeValidator:
        """Return a size validator instance."""
        return SizeValidator()

    @pytest.fixture
    def context(self) -> ValidationContext:
        """Return a validation context."""
        return ValidationContext(network_type=NetworkType.OGX, direction=MessageType.FORWARD)

    def test_validate_raw_payload_valid_size(self, validator, context):
        """Test validation with valid raw payload size."""
        data = {"RawPayload": "x" * (MAX_OGX_PAYLOAD_BYTES - 100)}
        result = validator.validate(data, context)
        assert result.is_valid

    def test_validate_raw_payload_oversized(
        self, validator: SizeValidator, context: ValidationContext
    ):
        """Test validation with oversized raw payload."""
        data = {"RawPayload": "x" * (MAX_OGX_PAYLOAD_BYTES + 1)}
        result = validator.validate(data, context)
        assert not result.is_valid
        assert "Raw payload size" in result.errors[0]
        assert hasattr(result, "current_size") and result.current_size > MAX_OGX_PAYLOAD_BYTES
        assert hasattr(result, "max_size") and result.max_size == MAX_OGX_PAYLOAD_BYTES

    def test_validate_raw_payload_edge_case(self, validator, context):
        """Test validation at raw payload size limit boundary."""
        # Test exactly at limit
        data = {"RawPayload": "x" * MAX_OGX_PAYLOAD_BYTES}
        result = validator.validate(data, context)
        assert result.is_valid

        # Test one byte over
        data = {"RawPayload": "x" * (MAX_OGX_PAYLOAD_BYTES + 1)}
        result = validator.validate(data, context)
        assert not result.is_valid
        assert "Raw payload size" in result.errors[0]

    def test_validate_json_payload(self, validator, context):
        """Test validation with JSON payload."""
        data = {
            "DestinationID": "test_id",
            "Payload": {"Name": "test_message", "SIN": 16, "MIN": 1, "Fields": []},
        }
        result = validator.validate(data, context)
        assert result.is_valid

    def test_validate_invalid_json_payload(self, validator, context):
        """Test validation with invalid JSON payload."""
        data = {"DestinationID": "test_id", "Payload": "not a json object"}  # Should be a dict
        result = validator.validate(data, context)
        assert not result.is_valid
        assert "Payload must be a JSON object" in result.errors[0]

    def test_validate_invalid_raw_payload(self, validator, context):
        """Test validation with invalid raw payload."""
        data = {"DestinationID": "test_id", "RawPayload": 123}  # Should be a string
        result = validator.validate(data, context)
        assert not result.is_valid
        assert "RawPayload must be a string" in result.errors[0]

    def test_validate_missing_payload(self, validator, context):
        """Test validation with no payload."""
        data = {
            "DestinationID": "test_id"
            # Missing both RawPayload and Payload
        }
        result = validator.validate(data, context)
        assert not result.is_valid
        assert "Message must contain either RawPayload or Payload" in result.errors[0]

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

    def test_validate_with_exception_handling(self, validator, context):
        """Test validation with an exception that triggers general error handling."""

        class BadString:
            def __len__(self):
                raise RuntimeError("Simulated error")

            def __str__(self):
                raise RuntimeError("Cannot convert to string")

        data = {"RawPayload": BadString()}
        result = validator.validate(data, context)
        assert not result.is_valid
        assert "Failed to validate message" in result.errors[0]


class TestOGxTransportValidator:
    """Test transport validation according to OGx-1.txt."""

    @pytest.fixture
    def validator(self) -> OGxTransportValidator:
        """Return a transport validator instance."""
        return OGxTransportValidator()

    @pytest.fixture
    def context(self) -> ValidationContext:
        """Return a validation context."""
        return ValidationContext(network_type=NetworkType.OGX, direction=MessageType.FORWARD)

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

    def test_validate_with_none_context(self, validator):
        """Test validation with None context."""
        result = validator.validate({"transport": "satellite"}, None)
        assert not result.is_valid
        assert "Missing message direction" in result.errors[0]

    def test_validate_with_none_context_direction(self, validator: OGxTransportValidator):
        """Test validation with None context direction."""
        # Create context with valid direction first, then modify for test
        context = ValidationContext(network_type=NetworkType.OGX, direction=MessageType.FORWARD)
        context.direction = None  # type: ignore  # Intentionally setting invalid type for test
        result = validator.validate({"transport": "satellite"}, context)
        assert not result.is_valid
        assert "Missing message direction" in result.errors[0]

    def test_validate_with_none_context_network_type(self, validator: OGxTransportValidator):
        """Test validation with None context network type."""
        # Create context with valid network_type first, then modify for test
        context = ValidationContext(network_type=NetworkType.OGX, direction=MessageType.FORWARD)
        context.network_type = None  # type: ignore  # Intentionally setting invalid type for test
        result = validator.validate({"transport": "satellite"}, context)
        assert not result.is_valid
        assert "Missing network type in context" in result.errors[0]

    def test_validate_with_invalid_network_type(self, validator):
        """Test validation with invalid network type."""
        context = ValidationContext(
            network_type=NetworkType.ISATDATA_PRO, direction=MessageType.FORWARD
        )
        result = validator.validate({"transport": "satellite"}, context)
        assert not result.is_valid
        assert "Invalid protocol: Expected OGx network" in result.errors[0]

    def test_validate_with_delayed_send_cellular(self, validator, context):
        """Test validation with delayed send options on cellular transport."""
        data = {"transport": "cellular", "DelayedSendOptions": {"DelayedSend": True}}
        result = validator.validate(data, context)
        assert not result.is_valid
        assert "Delayed send options not supported for cellular transport" in result.errors[0]

    def test_validate_with_non_string_transport(self, validator, context):
        """Test validation with non-string transport type."""
        result = validator.validate({"transport": 123}, context)  # Integer instead of string
        assert not result.is_valid
        assert "Invalid transport type" in result.errors[0]

    def test_validate_with_none_data(self, validator, context):
        """Test validation with None data."""
        result = validator.validate(None, context)
        assert not result.is_valid
        assert "Invalid data: None" in result.errors[0]

    def test_validate_with_non_dict_data(self, validator, context):
        """Test validation with non-dict data."""
        result = validator.validate("not a dict", context)
        assert not result.is_valid
        assert "Invalid data type: expected dictionary" in result.errors[0]

    def test_validate_with_invalid_direction(self, validator: OGxTransportValidator):
        """Test validation with invalid message direction."""
        # Create context with valid direction first, then modify for test
        context = ValidationContext(network_type=NetworkType.OGX, direction=MessageType.FORWARD)
        context.direction = "INVALID"  # type: ignore  # Intentionally setting invalid type for test
        result = validator.validate({"transport": "satellite"}, context)
        assert not result.is_valid
        assert "Invalid message direction" in result.errors[0]
