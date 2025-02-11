"""Unit tests for field validation according to OGWS-1.txt Section 5.1 Table 3.

Tests focus on basic field validation rules:
- Required properties (Name, Type)
- Value attribute requirements for basic types
- Type validation
- Dynamic/Property field validation
"""

from typing import Any, Dict

import pytest

from protocols.ogx.constants.message_types import MessageType
from protocols.ogx.validation.common.types import ValidationContext
from protocols.ogx.validation.common.validation_exceptions import ValidationError
from protocols.ogx.validation.message.field_validator import OGxFieldValidator


@pytest.fixture
def field_validator() -> OGxFieldValidator:
    """Provide field validator instance."""
    return OGxFieldValidator()


@pytest.fixture
def validation_context() -> ValidationContext:
    """Provide validation context."""
    return ValidationContext(network_type="OGx", direction=MessageType.FORWARD)


@pytest.fixture
def valid_field() -> Dict[str, Any]:
    """Provide valid field data for testing."""
    return {"Name": "test_field", "Type": "string", "Value": "test_value"}


class TestFieldValidator:
    """Test field validator implementation."""

    def test_validates_required_properties(
        self, field_validator: OGxFieldValidator, validation_context: ValidationContext
    ):
        """Test validation of required field properties."""
        # Missing required Name
        field_data = {"Type": "string", "Value": "test"}
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert "Name" in result.errors[0]

        # Missing required Type
        field_data = {"Name": "test", "Value": "test"}
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert "Type" in result.errors[0]

    def test_validates_field_type(
        self, field_validator: OGxFieldValidator, validation_context: ValidationContext
    ):
        """Test validation of field type."""
        # Invalid field type
        field_data = {"Name": "test", "Type": "invalid_type", "Value": "test"}
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert "Invalid field type" in result.errors[0]

    def test_validates_type_attribute(
        self, field_validator: OGxFieldValidator, validation_context: ValidationContext
    ):
        """Test validation of dynamic/property field type attributes."""
        # Dynamic field without type attribute
        field_data = {"Name": "test", "Type": "dynamic", "Value": "test"}
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert "TypeAttribute" in result.errors[0]

        # Dynamic field with invalid type attribute
        field_data = {
            "Name": "test",
            "Type": "dynamic",
            "TypeAttribute": "invalid",
            "Value": "test",
        }
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert "Invalid TypeAttribute" in result.errors[0]

        # Dynamic field with valid type attribute
        field_data = {
            "Name": "test",
            "Type": "dynamic",
            "TypeAttribute": "string",
            "Value": "test",
        }
        result = field_validator.validate(field_data, validation_context)
        assert result.is_valid

    def test_validates_field_values(
        self, field_validator: OGxFieldValidator, validation_context: ValidationContext
    ):
        """Test validation of field values against their types."""
        # Test unsigned int validation
        field_data = {"Name": "test", "Type": "unsignedint", "Value": -1}
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert "Invalid value for type FieldType.UNSIGNED_INT" in result.errors[0]

        # Test boolean validation
        field_data = {"Name": "test", "Type": "boolean", "Value": "not-a-bool"}
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert "Invalid value for type FieldType.BOOLEAN" in result.errors[0]

        # Test string validation
        field_data = {"Name": "test", "Type": "string", "Value": 123}
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert "Invalid value for type FieldType.STRING" in result.errors[0]

    def test_validates_value_requirements(
        self, field_validator: OGxFieldValidator, validation_context: ValidationContext
    ):
        """Test validation of Value attribute requirements."""
        # Basic type missing Value
        field_data = {"Name": "test", "Type": "string"}
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert "Value" in result.errors[0]

        # Array type with Value (should fail)
        field_data = {"Name": "test", "Type": "array", "Value": "test"}
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert "Array fields must not have Value attribute" in result.errors[0]

        # Message type with Value (should fail)
        field_data = {"Name": "test", "Type": "message", "Value": "test"}
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert "Message fields must not have Value attribute" in result.errors[0]

    def test_array_field_validation_with_missing_context(self, field_validator: OGxFieldValidator):
        """Test array field validation when context is missing."""
        field_data = {
            "Name": "test_array",
            "Type": "array",
            "Elements": [{"Index": 0, "Fields": []}],
        }

        # Clear the context
        field_validator.context = None

        result = field_validator.validate(field_data, None)
        assert not result.is_valid
        assert any("context is required" in error for error in result.errors)

    def test_array_field_with_invalid_elements(
        self, field_validator: OGxFieldValidator, validation_context: ValidationContext
    ):
        """Test array field validation with invalid elements."""
        field_data = {
            "Name": "test_array",
            "Type": "array",
            "Elements": [{"Invalid": "element"}],  # Missing required Index and Fields
        }

        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert len(result.errors) > 0

    def test_array_field_with_both_value_and_elements(
        self, field_validator: OGxFieldValidator, validation_context: ValidationContext
    ):
        """Test array field validation when both Value and Elements are present."""
        field_data = {
            "Name": "test_array",
            "Type": "array",
            "Value": "should not be here",
            "Elements": [{"Index": 0, "Fields": []}],
        }

        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert any("must not have Value attribute" in error for error in result.errors)

    def test_array_field_validation_error_propagation(
        self, field_validator: OGxFieldValidator, validation_context: ValidationContext
    ):
        """Test array field validation error propagation."""
        field_data = {
            "Name": "test_array",
            "Type": "array",
            "Elements": [
                {
                    "Index": 0,
                    "Fields": [
                        {
                            "Name": "test_field",
                            "Type": "unsignedint",
                            "Value": -1,
                        }  # Invalid value for unsigned int
                    ],
                }
            ],
        }

        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert len(result.errors) > 0

    def test_message_field_validation_error_paths(
        self, field_validator: OGxFieldValidator, validation_context: ValidationContext
    ):
        """Test message field validation error paths."""
        # Test with Value attribute (should fail)
        field_data = {
            "Name": "test_message",
            "Type": "message",
            "Value": "should not be here",
            "Message": {},
        }
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert any("must not have Value attribute" in error for error in result.errors)

        # Test with missing Message attribute
        field_data = {
            "Name": "test_message",
            "Type": "message",
        }
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert any("must have Message attribute" in error for error in result.errors)

    def test_message_field_validation_error_propagation(
        self, field_validator: OGxFieldValidator, validation_context: ValidationContext
    ):
        """Test message field validation error propagation."""
        field_data = {
            "Name": "test_message",
            "Type": "message",
            "Message": {
                "Name": "test_submessage",
                "Fields": [
                    {
                        "Name": "test_field",
                        "Type": "boolean",
                        "Value": "not_a_boolean",
                    }  # Invalid boolean value
                ],
            },
        }

        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert len(result.errors) > 0

    def test_dynamic_field_validation_paths(
        self, field_validator: OGxFieldValidator, validation_context: ValidationContext
    ):
        """Test dynamic field validation paths."""
        # Test dynamic field with valid type attribute and value
        field_data = {
            "Name": "test_dynamic",
            "Type": "dynamic",
            "TypeAttribute": "string",
            "Value": "test",
        }
        result = field_validator.validate(field_data, validation_context)
        assert result.is_valid

        # Test dynamic field with missing type attribute
        field_data = {"Name": "test_dynamic", "Type": "dynamic", "Value": "test"}
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert any("TypeAttribute" in error for error in result.errors)

        # Test dynamic field with invalid type attribute
        field_data = {
            "Name": "test_dynamic",
            "Type": "dynamic",
            "TypeAttribute": "invalid_type",
            "Value": "test",
        }
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert any("Invalid TypeAttribute" in error for error in result.errors)

        # Test dynamic field with valid type attribute but invalid value
        field_data = {
            "Name": "test_dynamic",
            "Type": "dynamic",
            "TypeAttribute": "boolean",
            "Value": "not a boolean",
        }
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert any("Invalid value" in error for error in result.errors)

    def test_field_validation_with_invalid_type_attribute(
        self, field_validator: OGxFieldValidator, validation_context: ValidationContext
    ):
        """Test field validation with invalid type attribute."""
        field_data = {
            "Name": "test_field",
            "Type": "dynamic",
            "TypeAttribute": "invalid_type",
            "Value": "test",
        }

        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert any("Invalid TypeAttribute" in error for error in result.errors)

    def test_array_field_with_missing_elements(
        self, field_validator: OGxFieldValidator, validation_context: ValidationContext
    ):
        """Test array field validation with missing Elements attribute."""
        field_data = {
            "Name": "test_array",
            "Type": "array",
        }

        result = field_validator.validate(field_data, validation_context)
        assert result.is_valid  # Elements is optional

    def test_message_field_with_missing_message(
        self, field_validator: OGxFieldValidator, validation_context: ValidationContext
    ):
        """Test message field validation with missing Message attribute."""
        field_data = {
            "Name": "test_message",
            "Type": "message",
        }

        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert any("must have Message attribute" in error for error in result.errors)

    def test_field_validation_with_unknown_type(
        self, field_validator: OGxFieldValidator, validation_context: ValidationContext
    ):
        """Test field validation with unknown field type."""
        field_data = {
            "Name": "test_field",
            "Type": "unknown",
            "Value": "test",
        }

        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert any("Invalid field type" in error for error in result.errors)

    def test_array_field_validation_error_handling(
        self, field_validator: OGxFieldValidator, validation_context: ValidationContext
    ):
        """Test array field validation error handling."""
        field_data = {
            "Name": "test_array",
            "Type": "array",
            "Elements": [
                {
                    "Index": 0,
                    "Fields": [
                        {
                            "Name": "test_field",
                            "Type": "unsignedint",
                            "Value": "not_a_number",  # Will cause ValueError
                        }
                    ],
                }
            ],
        }
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert any("Invalid value for type" in error for error in result.errors)

    def test_message_field_validation_error_handling(
        self, field_validator: OGxFieldValidator, validation_context: ValidationContext
    ):
        """Test message field validation error handling."""
        field_data = {
            "Name": "test_message",
            "Type": "message",
            "Message": {
                "Name": "test_submessage",
                "SIN": 16,
                "MIN": 1,
                "Fields": [
                    {
                        "Name": "test_field",
                        "Type": "unsignedint",
                        "Value": "not_a_number",  # Will cause ValueError
                    }
                ],
            },
        }
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert any("Invalid value for type" in error for error in result.errors)

    def test_validates_signed_int_field(
        self, field_validator: OGxFieldValidator, validation_context: ValidationContext
    ):
        """Test validation of signed integer fields."""
        # Test valid positive
        field_data = {"Name": "test", "Type": "signedint", "Value": "42"}
        result = field_validator.validate(field_data, validation_context)
        assert result.is_valid

        # Test valid negative
        field_data = {"Name": "test", "Type": "signedint", "Value": "-42"}
        result = field_validator.validate(field_data, validation_context)
        assert result.is_valid

        # Test invalid format
        field_data = {"Name": "test", "Type": "signedint", "Value": "not-a-number"}
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert "Invalid value for type FieldType.SIGNED_INT" in result.errors[0]

    def test_validates_enum_field(
        self, field_validator: OGxFieldValidator, validation_context: ValidationContext
    ):
        """Test validation of enum fields."""
        # Test valid enum value (string)
        field_data = {"Name": "test", "Type": "enum", "Value": "VALID_ENUM"}
        result = field_validator.validate(field_data, validation_context)
        assert result.is_valid

        # Test empty enum value
        field_data = {"Name": "test", "Type": "enum", "Value": ""}
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert "Invalid value for type FieldType.ENUM" in result.errors[0]

    def test_validates_data_field(
        self, field_validator: OGxFieldValidator, validation_context: ValidationContext
    ):
        """Test validation of data fields."""
        # Test valid base64 data
        field_data = {"Name": "test", "Type": "data", "Value": "SGVsbG8gV29ybGQ="}
        result = field_validator.validate(field_data, validation_context)
        assert result.is_valid

        # Test invalid data (not base64)
        field_data = {"Name": "test", "Type": "data", "Value": "not-base64!@#"}
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert "Invalid value for type FieldType.DATA" in result.errors[0]

    def test_validates_message_fields_without_context(self, field_validator: OGxFieldValidator):
        """Test validation of message fields when context is not provided."""
        # Should fail validation since context is required
        field_data = {
            "Name": "test",
            "Type": "message",
            "Message": {"SIN": 1, "MIN": 1, "Fields": []},
        }
        result = field_validator.validate(field_data, None)
        assert not result.is_valid
        assert "Validation context is required" in result.errors[0]

    def test_validates_array_fields_without_elements(
        self, field_validator: OGxFieldValidator, validation_context: ValidationContext
    ):
        """Test validation of array fields with missing Elements."""
        field_data = {"Name": "test", "Type": "array"}
        result = field_validator.validate(field_data, validation_context)
        assert result.is_valid  # Arrays can be empty according to spec

    def test_field_type_base64_validation_error_paths(
        self, field_validator: OGxFieldValidator, validation_context: ValidationContext
    ):
        """Test validation error paths for base64 data."""
        # Test with None value
        field_data = {"Name": "test", "Type": "data", "Value": None}
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert any("must be a base64 encoded string" in error for error in result.errors)

        # Test with non-string value
        field_data = {"Name": "test", "Type": "data", "Value": 123}
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert any("must be a base64 encoded string" in error for error in result.errors)

        # Test with invalid base64 string
        field_data = {"Name": "test", "Type": "data", "Value": "!!!invalid base64!!!"}
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert any("must be a valid base64 encoded string" in error for error in result.errors)

    def test_dynamic_field_with_missing_value(
        self, field_validator: OGxFieldValidator, validation_context: ValidationContext
    ):
        """Test dynamic field validation when Value is missing."""
        field_data = {
            "Name": "test_dynamic",
            "Type": "dynamic",
            "TypeAttribute": "string",
            # Value is missing
        }
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert any("Value" in error for error in result.errors)

    def test_message_field_without_message_content(
        self, field_validator: OGxFieldValidator, validation_context: ValidationContext
    ):
        """Test message field validation with empty Message content."""
        field_data = {
            "Name": "test_message",
            "Type": "message",
            "Message": {},  # Empty message content
        }
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert any("Message" in error for error in result.errors)

    def test_validate_method_error_paths(
        self, field_validator: OGxFieldValidator, validation_context: ValidationContext
    ):
        """Test error paths in validate method."""
        # Test with None data
        result = field_validator.validate(None, validation_context)  # line 114
        assert not result.is_valid
        assert any("required" in error for error in result.errors)

        # Test with completely invalid field data
        result = field_validator.validate({"invalid": "data"}, validation_context)
        assert not result.is_valid
        assert any("required" in error for error in result.errors)

    def test_validate_basic_field_error_paths(
        self, field_validator: OGxFieldValidator, validation_context: ValidationContext
    ):
        """Test basic field validation error paths."""
        # Test with missing Value attribute
        field_data = {"Name": "test", "Type": "string"}  # lines 218-219
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert any("Value" in error for error in result.errors)

    def test_validate_field_type_complete_paths(
        self, field_validator: OGxFieldValidator, validation_context: ValidationContext
    ):
        """Test all field type validation paths."""
        # Test with missing type attribute in dynamic field
        field_data = {
            "Name": "test",
            "Type": "dynamic",
            "TypeAttribute": None,
            "Value": "test",
        }  # line 226
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert any("TypeAttribute" in error for error in result.errors)

        # Test with invalid type conversion
        field_data = {
            "Name": "test",
            "Type": "dynamic",
            "TypeAttribute": "invalid",
            "Value": "test",
        }  # line 239
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert any("Invalid TypeAttribute" in error for error in result.errors)

        # Test field type validation exit
        field_data = {"Name": "test", "Type": "string", "Value": None}  # line 246
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert any("must be a string" in error for error in result.errors)

    def test_base64_validation_complete_paths(
        self, field_validator: OGxFieldValidator, validation_context: ValidationContext
    ):
        """Test all base64 validation paths."""
        # Test with invalid base64 string that raises different exception
        field_data = {"Name": "test", "Type": "data", "Value": "===invalid==="}  # line 267
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert any("base64" in error for error in result.errors)

    def test_error_propagation_paths(
        self, field_validator: OGxFieldValidator, validation_context: ValidationContext
    ):
        """Test error propagation through nested validation."""
        # Nested message validation error
        field_data = {
            "Name": "test_message",
            "Type": "message",
            "Message": {
                "SIN": 1,
                "MIN": 1,
                "Fields": [
                    {
                        "Name": "nested_field",
                        "Type": "dynamic",
                        "TypeAttribute": "invalid",  # This will cause error
                        "Value": "test",
                    }
                ],
            },
        }
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert any("In nested message" in error for error in result.errors)

        # Nested array validation error
        field_data = {
            "Name": "test_array",
            "Type": "array",
            "Elements": [
                {
                    "Index": 0,
                    "Fields": [
                        {
                            "Name": "nested_field",
                            "Type": "dynamic",
                            "TypeAttribute": "invalid",  # This will cause error
                            "Value": "test",
                        }
                    ],
                }
            ],
        }
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert any("In array element" in error for error in result.errors)

    def test_deep_nested_validation(
        self, field_validator: OGxFieldValidator, validation_context: ValidationContext
    ):
        """Test validation of deeply nested structures."""
        # Message within message within message
        field_data = {
            "Name": "outer_message",
            "Type": "message",
            "Message": {
                "SIN": 1,
                "MIN": 1,
                "Fields": [
                    {
                        "Name": "middle_message",
                        "Type": "message",
                        "Message": {
                            "SIN": 2,
                            "MIN": 2,
                            "Fields": [
                                {
                                    "Name": "inner_message",
                                    "Type": "message",
                                    "Message": {
                                        "SIN": 3,
                                        "MIN": 3,
                                        "Fields": [
                                            {
                                                "Name": "test_field",
                                                "Type": "string",
                                                "Value": 123,  # Invalid string value
                                            }
                                        ],
                                    },
                                }
                            ],
                        },
                    }
                ],
            },
        }
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert any("In nested message" in error for error in result.errors)

    def test_edge_case_exception_handling(
        self, field_validator: OGxFieldValidator, validation_context: ValidationContext
    ):
        """Test edge cases and exception handling."""
        # Test with invalid TypeAttribute type conversion
        field_data = {
            "Name": "test_field",
            "Type": "dynamic",
            "TypeAttribute": None,  # Should cause type conversion error
            "Value": "test",
        }
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert any("Invalid TypeAttribute" in error for error in result.errors)

        # Test with recursive message structure
        recursive_message = {"SIN": 1, "MIN": 1, "Fields": []}
        recursive_field = {
            "Name": "recursive_field",
            "Type": "message",
            "Message": recursive_message,
        }
        recursive_message["Fields"].append(recursive_field)  # Create recursive structure

        field_data = {"Name": "test_message", "Type": "message", "Message": recursive_message}
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid  # Should handle recursive structure without stack overflow

        # Test with extremely large nested structure
        deep_message = {"SIN": 1, "MIN": 1, "Fields": []}
        current = deep_message
        for i in range(1000):  # Create very deep nesting
            new_message = {"SIN": i + 2, "MIN": i + 2, "Fields": []}
            current["Fields"].append(
                {"Name": f"level_{i}", "Type": "message", "Message": new_message}
            )
            current = new_message

        field_data = {"Name": "test_message", "Type": "message", "Message": deep_message}
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid  # Should handle deep nesting gracefully

    def test_concurrent_validation_errors(
        self, field_validator: OGxFieldValidator, validation_context: ValidationContext
    ):
        """Test handling of multiple validation errors occurring simultaneously."""
        field_data = {
            "Name": "test_message",
            "Type": "message",
            "Message": {
                "Name": "test_inner_message",
                "SIN": 16,  # Valid SIN value between 16-255
                "MIN": 1,
                "Fields": [
                    {"Name": "field1", "Type": "string", "Value": 123},  # Invalid string value
                    {"Name": "field2", "Type": "unsignedint", "Value": -1},  # Invalid unsigned int
                    {"Name": "field3", "Type": "boolean", "Value": "invalid"},  # Invalid boolean
                ],
            },
        }
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid

        # Collect all error messages
        error_text = " ".join(result.errors)
        print(f"Actual errors: {result.errors}")  # Debug print

        # Check for all expected error types
        assert "must be a string" in error_text
        assert any(
            "must be non-negative" in err or "must be a valid integer" in err
            for err in result.errors
        )
        assert "must be a valid boolean" in error_text

        # Verify we have all three validation errors
        field_errors = [err for err in result.errors if "field" in err.lower()]
        assert len(field_errors) >= 3, f"Expected at least 3 field errors, got: {field_errors}"

    def test_validation_exit_paths(
        self, field_validator: OGxFieldValidator, validation_context: ValidationContext
    ):
        """Test validation early exit paths."""
        # Test exit on validation error (line 121)
        field_data = {"Type": "invalid"}  # Missing required Name
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert "Name" in result.errors[0]

        # Test exit on field type validation (line 151)
        field_data = {
            "Name": "test",
            "Type": "invalid_type",  # Invalid type will trigger early exit
        }
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert "Invalid field type" in result.errors[0]

        # Test exit on message validation (line 190)
        field_data = {
            "Name": "test",
            "Type": "message",
            "Message": None,  # Invalid message will trigger early exit
        }
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert "Message attribute" in result.errors[0]

    def test_dynamic_field_validation_complete(
        self, field_validator: OGxFieldValidator, validation_context: ValidationContext
    ):
        """Test complete dynamic field validation paths."""
        # Test dynamic field with empty type attribute (lines 225-226)
        field_data = {
            "Name": "test",
            "Type": "dynamic",
            "TypeAttribute": "",  # Empty type attribute
            "Value": "test",
        }
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert "Invalid TypeAttribute" in result.errors[0]

        # Test dynamic field with None value (line 233)
        field_data = {"Name": "test", "Type": "dynamic", "TypeAttribute": "string", "Value": None}
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert "must be a string" in str(result.errors)

    def test_field_type_validation_exits(
        self, field_validator: OGxFieldValidator, validation_context: ValidationContext
    ):
        """Test field type validation exit paths."""
        # Test type validation exit on unsignedint (line 235)
        field_data = {"Name": "test", "Type": "unsignedint", "Value": "not_a_number"}
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert "must be a valid integer" in result.errors[0]

        # Test type validation exit on signedint (line 246)
        field_data = {"Name": "test", "Type": "signedint", "Value": "invalid"}
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert "must be a valid integer" in result.errors[0]

        # Test type validation exit on enum (line 253)
        field_data = {"Name": "test", "Type": "enum", "Value": None}
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert "must be a non-empty string" in result.errors[0]

        # Test type validation exit on data with invalid base64 (line 274)
        field_data = {"Name": "test", "Type": "data", "Value": "======"}  # Invalid base64 padding
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert "must be a valid base64 encoded string" in result.errors[0]

    def test_validation_exception_propagation(
        self, field_validator: OGxFieldValidator, validation_context: ValidationContext
    ):
        """Test validation exception propagation through nested structures."""
        # Create deeply nested structure that will cause validation error propagation
        deep_field = {
            "Name": "test",
            "Type": "message",
            "Message": {
                "Name": "test_message",  # Add required Name field
                "SIN": 16,
                "MIN": 1,
                "Fields": [
                    {
                        "Name": "nested",
                        "Type": "array",
                        "Elements": [
                            {
                                "Index": 0,
                                "Fields": [
                                    {
                                        "Name": "deep_field",
                                        "Type": "dynamic",
                                        "TypeAttribute": "",  # Empty string will cause Invalid TypeAttribute error
                                        "Value": "test",
                                    }
                                ],
                            }
                        ],
                    }
                ],
            },
        }
        result = field_validator.validate(deep_field, validation_context)
        assert not result.is_valid
        assert len(result.errors) > 0

        # Print actual errors for debugging
        print(f"Actual errors: {result.errors}")

        # Verify error propagation through nested structure
        # The error should propagate through message -> array -> field
        nested_errors = [err for err in result.errors if "nested" in err.lower()]
        assert len(nested_errors) > 0, f"Expected nested validation errors, got: {result.errors}"
        assert any(
            "Invalid TypeAttribute" in err for err in result.errors
        ), f"Expected TypeAttribute error in: {result.errors}"

    def test_deep_exit_paths(
        self, field_validator: OGxFieldValidator, validation_context: ValidationContext
    ):
        """Test deep validation exit paths that are hard to reach."""
        # Test line 121 exit - Validation error in array field
        field_data = {
            "Name": "test",
            "Type": "array",
            "Elements": [{"Index": 0, "Fields": None}],  # Invalid Fields value
        }
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert any("must be an array" in err for err in result.errors)

        # Test line 151 exit - Field type validation with null values
        field_data = {
            "Name": "test",
            "Type": "",  # Empty type should trigger validation exit
        }
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert any("Invalid field type" in err for err in result.errors)

        # Test line 190 exit - Message validation with invalid inner message
        field_data = {
            "Name": "test",
            "Type": "message",
            "Message": {"Name": "inner", "SIN": None, "MIN": 1, "Fields": []},  # Invalid SIN
        }
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid

    def test_complex_validation_paths(
        self, field_validator: OGxFieldValidator, validation_context: ValidationContext
    ):
        """Test complex validation paths to cover remaining lines."""
        # Test lines 225-226, 233 - Dynamic field edge cases
        field_data = {
            "Name": "test",
            "Type": "dynamic",
            "TypeAttribute": "unsignedint",
            "Value": None,  # This hits line 233
        }
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert any("must be a valid integer" in err for err in result.errors)

        # Rest of test remains unchanged
        # Test line 235 exit - Unsigned int validation with edge case
        field_data = {
            "Name": "test",
            "Type": "unsignedint",
            "Value": [],  # Invalid type should trigger TypeError path
        }
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert any("must be a valid integer" in err for err in result.errors)

        # Test line 246 exit - String conversion failure in signed int
        field_data = {
            "Name": "test",
            "Type": "signedint",
            "Value": {},  # Invalid type should trigger TypeError path
        }
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert any("must be a valid integer" in err for err in result.errors)

        # Test line 253 exit - Enum validation with null
        field_data = {
            "Name": "test",
            "Type": "enum",
            "Value": None,  # Should trigger enum validation exit
        }
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert any("must be a non-empty string" in err for err in result.errors)

        # Test line 274 exit - Base64 validation with padding error
        field_data = {"Name": "test", "Type": "data", "Value": "SGVsbG8="[:-1]}  # Invalid padding
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert any("must be a valid base64 encoded string" in err for err in result.errors)

    def test_nested_validation_failures(
        self, field_validator: OGxFieldValidator, validation_context: ValidationContext
    ):
        """Test nested validation failures that trigger exit paths."""
        # Create a deeply nested structure that triggers multiple validation paths
        field_data = {
            "Name": "test",
            "Type": "message",
            "Message": {
                "Name": "outer",
                "SIN": 16,
                "MIN": 1,
                "Fields": [
                    {
                        "Name": "array_field",
                        "Type": "array",
                        "Elements": [
                            {
                                "Index": 0,
                                "Fields": [
                                    {
                                        "Name": "dynamic_field",
                                        "Type": "dynamic",
                                        "TypeAttribute": "unsignedint",
                                        "Value": [],  # Invalid value type
                                    }
                                ],
                            }
                        ],
                    }
                ],
            },
        }
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        print(f"Actual errors: {result.errors}")  # Print errors for debugging

        # Should have multiple errors propagating up
        assert len(result.errors) > 0
        # Check for nested error propagation
        assert any("must be a valid integer" in err for err in result.errors)

    def test_forced_exit_paths(
        self, field_validator: OGxFieldValidator, validation_context: ValidationContext, mocker
    ):
        """Test forced exit paths by mocking exceptions."""
        # Mock validate_array to raise exception for line 121 exit
        mocker.patch.object(
            field_validator.element_validator,
            "validate_array",
            side_effect=ValidationError("Forced array error"),
        )

        field_data = {"Name": "test", "Type": "array", "Elements": []}
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert "Forced array error" in result.errors[0]

        # Mock _validate_field_type to raise exception for line 151 exit
        mocker.patch.object(
            field_validator,
            "_validate_field_type",
            side_effect=ValidationError("Forced type error"),
        )

        field_data = {"Name": "test", "Type": "string", "Value": "test"}
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert "Forced type error" in result.errors[0]

        # Create chain of exceptions to hit line 190 exit
        from protocols.ogx.validation.message.message_validator import OGxMessageValidator

        mocker.patch.object(
            OGxMessageValidator, "validate", side_effect=ValidationError("Forced message error")
        )

        field_data = {
            "Name": "test",
            "Type": "message",
            "Message": {"Name": "inner", "SIN": 16, "MIN": 1, "Fields": []},
        }
        result = field_validator.validate(field_data, validation_context)
        assert not result.is_valid
        assert "Forced message error" in result.errors[0]
