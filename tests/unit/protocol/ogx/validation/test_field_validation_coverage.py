"""Additional tests to improve coverage of field_validator.py.

These tests focus on edge cases and error paths that were previously uncovered:
- Error propagation in nested structures
- Import error handling
- Dynamic field validation edge cases
- Field type validation error paths
"""

import pytest
from unittest.mock import Mock, patch

from protocols.ogx.constants.message_types import MessageType
from protocols.ogx.validation.common.types import ValidationContext
from protocols.ogx.validation.common.validation_exceptions import ValidationError
from protocols.ogx.validation.message.field_validator import OGxFieldValidator
from protocols.ogx.constants.field_types import FieldType


@pytest.fixture
def field_validator() -> OGxFieldValidator:
    """Provide field validator instance."""
    return OGxFieldValidator()


@pytest.fixture
def validation_context() -> ValidationContext:
    """Provide validation context."""
    return ValidationContext(network_type="OGx", direction=MessageType.FORWARD)


class TestFieldValidatorCoverage:
    """Additional tests to improve field validator coverage."""

    def test_message_field_import_error(self, field_validator, validation_context):
        """Test message field validation when message validator import fails."""
        field_data = {
            "Name": "test",
            "Type": "message",
            "Message": {"Name": "inner", "SIN": 16, "MIN": 1, "Fields": []},
        }

        field_validator.context = validation_context
        # Mock the message validator import to raise ImportError
        with patch(
            "protocols.ogx.validation.message.field_validator.OGxMessageValidator",
            side_effect=ImportError("Failed to import"),
        ):
            with pytest.raises(ValidationError) as exc:
                field_validator._validate_message_field(field_data)
            assert "Message validation unavailable" in str(exc.value)

    def test_dynamic_field_type_resolution_error(self, field_validator, validation_context):
        """Test dynamic field validation when type resolution fails."""
        field_data = {
            "Name": "test",
            "Type": "dynamic",
            "TypeAttribute": "invalid_type",
            "Value": "test",
        }
        field_validator.context = validation_context
        with pytest.raises(ValidationError) as exc:
            field_validator._validate_dynamic_field(FieldType.DYNAMIC, field_data)
        assert "Invalid dynamic field: TypeAttribute invalid_type not allowed" in str(exc.value)

    def test_field_type_validation_unexpected_error(self, field_validator, validation_context):
        """Test field type validation with unexpected error."""

        class BadValue:
            def __int__(self):
                raise RuntimeError("Unexpected error")

        field_data = {
            "Name": "test",
            "Type": "unsignedint",
            "Value": BadValue(),
        }
        field_validator.context = validation_context
        with pytest.raises(ValidationError) as exc:
            field_validator._validate_field_type(
                field_type=FieldType.UNSIGNED_INT, value=BadValue(), check_null=True
            )
        assert "Unexpected error" in str(exc.value)

    def test_nested_message_validation_error(self, field_validator, validation_context):
        """Test validation of nested message with validation error."""
        field_data = {
            "Name": "test",
            "Type": "message",
            "Message": {
                "Name": "inner",
                "SIN": 16,
                "MIN": 1,
                "Fields": [
                    {
                        "Name": "nested",
                        "Type": "unsignedint",
                        "Value": -1,  # Invalid value
                    }
                ],
            },
        }
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert "In nested message: Field validation error" in result.errors[0]

    def test_dynamic_field_null_type_attribute(self, field_validator, validation_context):
        """Test dynamic field with null type attribute."""
        field_data = {
            "Name": "test",
            "Type": "dynamic",
            "TypeAttribute": None,
            "Value": "test",
        }
        field_validator.context = validation_context
        with pytest.raises(ValidationError) as exc:
            field_validator._validate_dynamic_field(FieldType.DYNAMIC, field_data)
        assert "Missing required field TypeAttribute" in str(exc.value)

    def test_field_type_validation_with_none_check(self, field_validator, validation_context):
        """Test field type validation with None check disabled."""
        field_data = {
            "Name": "test",
            "Type": "string",
            "Value": None,
        }
        field_validator.context = validation_context
        with pytest.raises(ValidationError) as exc:
            field_validator._validate_field_type(
                field_type=FieldType.STRING, value=field_data["Value"], check_null=False
            )
        assert "Invalid string field: Value must be a string" in str(exc.value)

    def test_array_field_with_invalid_nested_field(self, field_validator, validation_context):
        """Test array field with invalid nested field."""
        field_data = {
            "Name": "test",
            "Type": "array",
            "Elements": [
                {
                    "Index": 0,
                    "Fields": [
                        {
                            "Name": "nested",
                            "Type": "dynamic",
                            "TypeAttribute": "invalid",
                            "Value": "test",
                        }
                    ],
                }
            ],
        }
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert "Invalid dynamic field: TypeAttribute invalid not allowed" in str(result.errors[0])

    def test_message_field_without_context(self, field_validator):
        """Test message field validation without context."""
        field_data = {
            "Name": "test",
            "Type": "message",
            "Message": {"Name": "inner", "SIN": 16, "MIN": 1, "Fields": []},
        }
        with pytest.raises(ValidationError) as exc:
            field_validator._validate_message_field(field_data)
        assert "Invalid message field: Validation context required" in str(exc.value)

    def test_dynamic_field_with_empty_type_attribute(self, field_validator, validation_context):
        """Test dynamic field with empty type attribute."""
        field_data = {
            "Name": "test",
            "Type": "dynamic",
            "TypeAttribute": "",
            "Value": "test",
        }
        field_validator.context = validation_context
        with pytest.raises(ValidationError) as exc:
            field_validator._validate_dynamic_field(FieldType.DYNAMIC, field_data)
        assert "Invalid dynamic field: Missing required field TypeAttribute" in str(exc.value)
