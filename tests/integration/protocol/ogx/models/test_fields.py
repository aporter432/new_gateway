"""Integration tests for field validation according to OGWS-1.txt Section 5 and Table 3."""

import pytest

from protocols.ogx.constants import FieldType
from protocols.ogx.constants.message_types import MessageType
from protocols.ogx.models import Element, Field, Message
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


class TestFieldValidation:
    """Test field validation against OGWS-1.txt rules."""

    def test_unsigned_int_validation(
        self, field_validator: OGxFieldValidator, validation_context: ValidationContext
    ):
        """Test validation of unsigned integer fields."""
        # Test invalid negative value
        with pytest.raises(ValidationError):
            field_data = {"Name": "count", "Type": "unsignedint", "Value": -1}
            result = field_validator.validate(field_data, validation_context)
            if not result.is_valid:
                raise ValidationError(result.errors[0])

    def test_array_field_validation(
        self, field_validator: OGxFieldValidator, validation_context: ValidationContext
    ):
        """Test validation of array field constraints."""
        with pytest.raises(ValidationError):
            field_data = {"Name": "invalid", "Type": "array", "Value": "test"}
            result = field_validator.validate(field_data, validation_context)
            if not result.is_valid:
                raise ValidationError(result.errors[0])

    def test_message_field_validation(
        self, field_validator: OGxFieldValidator, validation_context: ValidationContext
    ):
        """Test validation of message field constraints."""
        with pytest.raises(ValidationError):
            field_data = {"Name": "invalid", "Type": "message", "Value": "test"}
            result = field_validator.validate(field_data, validation_context)
            if not result.is_valid:
                raise ValidationError(result.errors[0])
