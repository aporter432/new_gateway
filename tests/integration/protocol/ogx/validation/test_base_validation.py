"""Integration tests for base validation according to OGWS-1.txt Section 5."""

import pytest

from protocols.ogx.constants.message_types import MessageType
from protocols.ogx.validation.common.validation_exceptions import ValidationError
from protocols.ogx.validation.common.types import ValidationContext
from protocols.ogx.validation.message.field_validator import OGxFieldValidator


@pytest.fixture
def field_validator() -> OGxFieldValidator:
    """Provide configured field validator."""
    return OGxFieldValidator()


@pytest.fixture
def validation_context() -> ValidationContext:
    """Provide validation context for tests."""
    return ValidationContext(network_type="OGx", direction=MessageType.FORWARD)


class TestBaseValidation:
    """Test base validation requirements from OGWS-1.txt."""

    def test_required_field_properties(self, field_validator, validation_context):
        """Test validation of required field properties (Name, Type)."""
        # Missing Name
        with pytest.raises(ValidationError, match=".*missing required Name.*"):
            field_data = {"Type": "string", "Value": "test"}
            field_validator.validate(field_data, validation_context)

        # Missing Type
        with pytest.raises(ValidationError, match=".*missing required Type.*"):
            field_data = {"Name": "test", "Value": "test"}
            field_validator.validate(field_data, validation_context)

        # Empty Name
        with pytest.raises(ValidationError, match=".*Name cannot be empty.*"):
            field_data = {"Name": "", "Type": "string", "Value": "test"}
            field_validator.validate(field_data, validation_context)

    def test_null_input_validation(self, field_validator, validation_context):
        """Test validation of null input."""
        with pytest.raises(ValidationError, match=".*Required field data missing.*"):
            field_validator.validate(None, validation_context)

    def test_empty_input_validation(self, field_validator, validation_context):
        """Test validation of empty input."""
        with pytest.raises(ValidationError, match=".*missing required.*"):
            field_validator.validate({}, validation_context)
