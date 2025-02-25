"""Unit tests for field validation.

This module tests field validation according to OGx-1.txt.
"""

import pytest

from Protexis_Command.protocols.ogx.constants.ogx_error_codes import GatewayErrorCode
from Protexis_Command.protocols.ogx.constants.ogx_field_types import FieldType
from Protexis_Command.protocols.ogx.constants.ogx_message_types import MessageType
from Protexis_Command.protocols.ogx.constants.ogx_network_types import NetworkType
from Protexis_Command.protocols.ogx.validation.ogx_validation_exceptions import ValidationError
from Protexis_Command.protocols.ogx.validation.validators.ogx_field_validator import (
    OGxFieldValidator,
)
from Protexis_Command.protocols.ogx.validation.validators.ogx_type_validator import (
    ValidationContext,
)


@pytest.fixture
def field_validator() -> OGxFieldValidator:
    """Provide field validator instance."""
    return OGxFieldValidator()


@pytest.fixture
def context() -> ValidationContext:
    """Provide test validation context."""
    return ValidationContext(network_type=NetworkType.OGX, direction=MessageType.FORWARD)


class TestFieldValidation:
    """Unit tests for field validation per OGx-1.txt Section 5.1 Table 3."""

    class TestRequiredProperties:
        """Test required field properties validation."""

        def test_missing_required_fields(self, field_validator):
            """Test missing Name and Type properties."""
            # Missing Name
            result = field_validator.validate({"Type": "string"}, None)
            assert not result.is_valid
            assert "Missing required field fields: Name" in result.errors[0]

            # Missing Type
            result = field_validator.validate({"Name": "test"}, None)
            assert not result.is_valid
            assert "Missing required field fields: Type" in result.errors[0]

        def test_none_input(self, field_validator):
            """Test None input data."""
            result = field_validator.validate(None, None)
            assert not result.is_valid
            assert "Required field data missing" in result.errors[0]

    class TestBasicTypes:
        """Test basic field type validation."""

        @pytest.mark.parametrize(
            "field_type,valid_value,invalid_value,error_msg",
            [
                (FieldType.STRING, "test", 123, "must be a string"),
                (FieldType.BOOLEAN, True, "invalid", "must be a boolean"),
                (FieldType.UNSIGNED_INT, 42, -1, "must be non-negative"),
                (FieldType.UNSIGNED_INT, 42, "not_a_number", "must be an integer"),
                (FieldType.SIGNED_INT, -42, "not_int", "must be an integer"),
                (FieldType.SIGNED_INT, -42, object(), "must be an integer"),
                (FieldType.ENUM, "VALID", "", "must be a non-empty string"),
                (FieldType.DATA, "YWJj", "invalid", "Value must be a valid base64 encoded string"),
            ],
        )
        def test_basic_field_validation(
            self, field_validator, field_type, valid_value, invalid_value, error_msg
        ):
            """Test validation of basic field types."""
            # Test valid value
            field = {"Name": "test", "Type": field_type.value, "Value": valid_value}
            result = field_validator.validate(field, None)
            assert result.is_valid

            # Test invalid value
            field["Value"] = invalid_value
            result = field_validator.validate(field, None)
            assert not result.is_valid
            assert error_msg in result.errors[0]

        def test_missing_value(self, field_validator):
            """Test missing Value for basic field types."""
            for field_type in FieldType:
                if field_type in (
                    FieldType.ARRAY,
                    FieldType.MESSAGE,
                    FieldType.DYNAMIC,
                    FieldType.PROPERTY,
                ):
                    continue

                field = {"Name": "test", "Type": field_type.value}
                result = field_validator.validate(field, None)
                assert not result.is_valid
                assert "Missing required field fields: Value" in result.errors[0]

        @pytest.mark.parametrize("bool_value", ["true", "false", "True", "False", "1", "0"])
        def test_boolean_string_values(self, field_validator, bool_value):
            """Test boolean field accepts valid string representations."""
            field = {"Name": "test", "Type": FieldType.BOOLEAN.value, "Value": bool_value}
            result = field_validator.validate(field, None)
            assert result.is_valid

        @pytest.mark.parametrize(
            "str_value,expected",
            [
                ("42", 42),
                ("3.14", 3),  # Float strings should be converted to int
                ("-123", -123),
            ],
        )
        def test_numeric_string_conversion(self, field_validator, str_value, expected):
            """Test numeric fields handle string inputs correctly."""
            field = {"Name": "test", "Type": FieldType.SIGNED_INT.value, "Value": str_value}
            result = field_validator.validate(field, None)
            assert result.is_valid

        def test_empty_base64(self, field_validator):
            """Test empty string is valid base64."""
            field = {"Name": "test", "Type": FieldType.DATA.value, "Value": ""}
            result = field_validator.validate(field, None)
            assert result.is_valid

        def test_invalid_base64_padding(self, field_validator):
            """Test base64 padding validation."""
            field = {
                "Name": "test",
                "Type": FieldType.DATA.value,
                "Value": "invalid_base64",  # Length not multiple of 4
            }
            result = field_validator.validate(field, None)
            assert not result.is_valid
            assert "Value must be a valid base64 encoded string" in result.errors[0]

    class TestArrayFields:
        """Test array field validation."""

        def test_value_not_allowed(self, field_validator):
            """Test Value attribute not allowed in array fields."""
            field = {"Name": "test", "Type": "array", "Value": "not_allowed"}
            result = field_validator.validate(field, None)
            assert not result.is_valid
            assert "Value attribute not allowed" in result.errors[0]

        def test_empty_elements(self, field_validator):
            """Test empty Elements list is valid."""
            field = {"Name": "test", "Type": "array", "Elements": []}
            result = field_validator.validate(field, None)
            assert result.is_valid

        def test_invalid_elements_type(self, field_validator):
            """Test Elements must be a list."""
            field = {"Name": "test", "Type": "array", "Elements": "not_a_list"}
            result = field_validator.validate(field, None)
            assert not result.is_valid
            assert "Elements must be a list" in result.errors[0]

        def test_element_structure(self, field_validator):
            """Test element structure validation."""
            # Test invalid index type
            field = {
                "Name": "test",
                "Type": "array",
                "Elements": [
                    {"Index": "3", "Fields": []},  # Invalid Index type (hits line 181)
                ],
            }
            result = field_validator.validate(field, None)
            assert not result.is_valid
            assert "Index must be an integer" in str(result.errors)

            # Test non-sequential indices (this is checked before duplicates)
            field = {
                "Name": "test",
                "Type": "array",
                "Elements": [
                    {"Index": 1, "Fields": []},  # Should be 0
                ],
            }
            result = field_validator.validate(field, None)
            assert not result.is_valid
            assert "Index must be 0" in str(result.errors)

            # Test missing Fields
            field = {
                "Name": "test",
                "Type": "array",
                "Elements": [
                    {"Index": 0},  # Missing Fields (hits line 203)
                ],
            }
            result = field_validator.validate(field, None)
            assert not result.is_valid
            assert "Missing required field Fields" in str(result.errors)

            # Test invalid Fields type
            field = {
                "Name": "test",
                "Type": "array",
                "Elements": [
                    {"Index": 0, "Fields": "not_a_list"},  # Invalid Fields type (hits line 210)
                ],
            }
            result = field_validator.validate(field, None)
            assert not result.is_valid
            assert "Fields must be a list" in str(result.errors)

        def test_sequential_indices(self, field_validator):
            """Test indices must be sequential starting from 0."""
            field = {
                "Name": "test",
                "Type": "array",
                "Elements": [{"Index": 1, "Fields": []}, {"Index": 2, "Fields": []}],  # Should be 0
            }
            result = field_validator.validate(field, None)
            assert not result.is_valid
            assert "Index must be 0" in result.errors[0]

        def test_array_validation_error_paths(self, field_validator):
            """Test array field validation error paths."""
            # Test invalid element type
            field = {"Name": "test", "Type": "array", "Elements": [123]}  # Not a dict
            result = field_validator.validate(field, None)
            assert not result.is_valid
            assert "Must be a dictionary" in result.errors[0]

            # Test invalid field in element
            field = {
                "Name": "test",
                "Type": "array",
                "Elements": [
                    {"Index": 0, "Fields": [{"Name": "test", "Type": "string"}]}
                ],  # Missing Value
            }
            result = field_validator.validate(field, None)
            assert not result.is_valid
            assert "Missing required field fields: Value" in result.errors[0]

    class TestMessageFields:
        """Test message field validation."""

        def test_value_not_allowed(self, field_validator, context):
            """Test Value attribute not allowed in message fields."""
            field = {
                "Name": "test",
                "Type": "message",
                "Value": "not_allowed",
                "Message": {"Name": "inner", "SIN": 16, "MIN": 1, "Fields": []},
            }
            result = field_validator.validate(field, context)
            assert not result.is_valid
            assert "Value attribute not allowed" in result.errors[0]

        def test_missing_message(self, field_validator, context):
            """Test Message attribute is required."""
            field = {"Name": "test", "Type": "message"}
            result = field_validator.validate(field, context)
            assert not result.is_valid
            assert "Missing required field Message" in result.errors[0]

        def test_invalid_message_type(self, field_validator, context):
            """Test Message must be a dictionary."""
            field = {"Name": "test", "Type": "message", "Message": "not_a_dict"}
            result = field_validator.validate(field, context)
            assert not result.is_valid
            assert "Message must be a non-empty dictionary" in result.errors[0]

        def test_required_message_fields(self, field_validator, context):
            """Test required fields in Message."""
            test_cases = [
                ({"Name": "inner", "MIN": 1, "Fields": []}, "SIN"),
                ({"Name": "inner", "SIN": 16, "Fields": []}, "MIN"),
                ({"Name": "inner", "SIN": 16, "MIN": 1}, "Fields"),
            ]
            for message, missing_field in test_cases:
                field = {"Name": "test", "Type": "message", "Message": message}
                result = field_validator.validate(field, context)
                assert not result.is_valid
                assert (
                    f"Validation error: Missing required fields: {missing_field}"
                    in result.errors[0]
                )

        def test_context_required(self, field_validator):
            """Test context is required for message validation."""
            field = {
                "Name": "test",
                "Type": "message",
                "Message": {"Name": "inner", "SIN": 16, "MIN": 1, "Fields": []},
            }
            result = field_validator.validate(field, None)
            assert not result.is_valid
            assert "Validation context required" in result.errors[0]

        def test_message_validation_error_handling(self, field_validator, context, mocker):
            """Test message validation error handling."""
            # Mock OGxStructureValidator to raise ImportError
            mocker.patch(
                "Protexis_Command.protocols.ogx.validation.validators.ogx_field_validator.OGxStructureValidator",
                side_effect=ImportError("Test import error"),
            )

            field = {
                "Name": "test",
                "Type": "message",
                "Message": {"Name": "inner", "SIN": 16, "MIN": 1, "Fields": []},
            }
            result = field_validator.validate(field, context)
            assert not result.is_valid
            assert "Message validation unavailable: Test import error" in result.errors[0]

        def test_message_field_validation_error_paths(self, field_validator, context):
            """Test message field validation error paths."""
            # Test invalid message field type
            field = {
                "Name": "test",
                "Type": "message",
                "Message": {"Name": "inner", "SIN": "not_int", "MIN": 1, "Fields": []},
            }
            result = field_validator.validate(field, context)
            assert not result.is_valid
            assert "SIN must be an integer" in result.errors[0]

    class TestDynamicFields:
        """Test dynamic field validation."""

        def test_type_attribute_required(self, field_validator):
            """Test TypeAttribute is required for dynamic fields."""
            field = {"Name": "test", "Type": "dynamic", "Value": "test"}
            result = field_validator.validate(field, None)
            assert not result.is_valid
            assert "Missing required field TypeAttribute" in result.errors[0]

        def test_invalid_type_attribute(self, field_validator):
            """Test TypeAttribute must be a valid basic type."""
            field = {
                "Name": "test",
                "Type": "dynamic",
                "TypeAttribute": "invalid_type",
                "Value": "test",
            }
            result = field_validator.validate(field, None)
            assert not result.is_valid
            assert "TypeAttribute invalid_type not allowed" in result.errors[0]

        def test_value_matches_type_attribute(self, field_validator):
            """Test Value must match TypeAttribute type."""
            field = {
                "Name": "test",
                "Type": "dynamic",
                "TypeAttribute": "string",
                "Value": 123,  # Should be string
            }
            result = field_validator.validate(field, None)
            assert not result.is_valid
            assert "must be a string" in result.errors[0]

        def test_property_field_validation(self, field_validator):
            """Test property field validation (same rules as dynamic)."""
            field = {
                "Name": "test",
                "Type": "property",
                "TypeAttribute": "boolean",
                "Value": "not_a_boolean",
            }
            result = field_validator.validate(field, None)
            assert not result.is_valid
            assert "must be a boolean" in result.errors[0]

        def test_dynamic_field_type_resolution(self, field_validator):
            """Test dynamic field type resolution with string values."""
            field = {
                "Name": "test",
                "Type": "dynamic",
                "TypeAttribute": "string",
                "Value": 123,  # Should be converted to string
            }
            result = field_validator.validate(field, None)
            assert not result.is_valid
            assert "must be a string" in result.errors[0]

        def test_unexpected_error_handling(self, field_validator, mocker):
            """Test handling of unexpected errors during validation."""
            # Mock _validate_field_by_type to raise ValidationError
            mocker.patch.object(
                field_validator,
                "_validate_field_by_type",
                side_effect=ValidationError("Test error", GatewayErrorCode.INVALID_FIELD_FORMAT),
            )

            field = {"Name": "test", "Type": "string", "Value": "test"}
            result = field_validator.validate(field, None)
            assert not result.is_valid
            assert "Test error" in result.errors[0]

        def test_dynamic_field_validation_error_paths(self, field_validator):
            """Test dynamic field validation error paths."""
            # Test missing value after type validation
            field = {"Name": "test", "Type": "dynamic", "TypeAttribute": "string", "Value": None}
            result = field_validator.validate(field, None)
            assert not result.is_valid
            assert "Value must be a string" in result.errors[0]

            # Test invalid type attribute value
            field = {"Name": "test", "Type": "dynamic", "TypeAttribute": "invalid", "Value": "test"}
            result = field_validator.validate(field, None)
            assert not result.is_valid
            assert "TypeAttribute invalid not allowed" in result.errors[0]
