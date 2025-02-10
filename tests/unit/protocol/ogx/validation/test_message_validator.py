"""Tests for OGx message validation"""

import pytest

from protocols.ogx.validation.json.message_validator import OGxMessageValidator
from protocols.ogx.validation.common.exceptions import ValidationError


class TestOGxMessageValidator:
    """Test suite for OGx message validator functionality.

    Tests validation of message structure, field types, and error handling
    according to the N214 specification.
    """

    @pytest.fixture
    def validator(self):
        """Create a message validator instance for testing.

        Returns:
            OGxMessageValidator: A fresh validator instance for each test.
        """
        return OGxMessageValidator()

    @pytest.fixture
    def valid_message(self):
        """Create a valid message fixture for testing.

        Returns:
            dict: A dictionary representing a valid OGx message with all required fields.
        """
        return {
            "Name": "test_message",
            "SIN": 16,
            "MIN": 1,
            "Fields": [{"Name": "field1", "Type": "string", "Value": "test"}],
        }

    def test_validate_valid_message(self, validator, valid_message):
        """Test validation of a valid message structure"""
        validator.validate_message(valid_message)  # Should not raise

    def test_validate_missing_required_fields(self, validator):
        """Test validation of message with missing required fields"""
        invalid_message = {"Name": "test_message", "Fields": []}  # Missing SIN and MIN
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_message(invalid_message)
        assert ValidationError.MISSING_REQUIRED_FIELD == exc_info.value.error_code

    def test_validate_invalid_sin_min_types(self, validator, valid_message):
        """Test validation of invalid SIN/MIN types"""
        # Test invalid SIN
        valid_message["SIN"] = "not_an_int"
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_message(valid_message)
        assert ValidationError.INVALID_FIELD_VALUE == exc_info.value.error_code

        # Test invalid MIN
        valid_message["SIN"] = 16
        valid_message["MIN"] = "not_an_int"
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_message(valid_message)
        assert ValidationError.INVALID_FIELD_VALUE == exc_info.value.error_code

        # Test negative SIN
        valid_message["MIN"] = 1
        valid_message["SIN"] = -1
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_message(valid_message)
        assert ValidationError.INVALID_FIELD_VALUE == exc_info.value.error_code

        # Test negative MIN
        valid_message["SIN"] = 16
        valid_message["MIN"] = -1
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_message(valid_message)
        assert ValidationError.INVALID_FIELD_VALUE == exc_info.value.error_code

    def test_validate_invalid_name_type(self, validator, valid_message):
        """Test validation of invalid Name type"""
        valid_message["Name"] = 123  # Should be string
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_message(valid_message)
        assert ValidationError.INVALID_FIELD_VALUE == exc_info.value.error_code

    def test_validate_invalid_fields_type(self, validator, valid_message):
        """Test validation of invalid Fields type"""
        valid_message["Fields"] = "not_a_list"
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_message(valid_message)
        assert ValidationError.INVALID_MESSAGE_FORMAT == exc_info.value.error_code

    def test_validate_nested_elements(self, validator):
        """Test validation of nested elements in fields"""
        message = {
            "Name": "test_message",
            "SIN": 16,
            "MIN": 1,
            "Fields": [
                {
                    "Name": "array_field",
                    "Type": "array",
                    "Elements": [
                        {
                            "Index": 0,
                            "Fields": [{"Name": "sub_field", "Type": "string", "Value": "test"}],
                        }
                    ],
                }
            ],
        }
        validator.validate_message(message)  # Should not raise

        # Test invalid element index
        message["Fields"][0]["Elements"][0]["Index"] = "not_an_int"
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_message(message)
        assert ValidationError.INVALID_ELEMENT_FORMAT == exc_info.value.error_code

        # Test missing element fields
        message["Fields"][0]["Elements"][0] = {"Index": 0}  # Missing Fields
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_message(message)
        assert ValidationError.MISSING_REQUIRED_FIELD == exc_info.value.error_code

        # Test invalid element fields type
        message["Fields"][0]["Elements"][0] = {"Index": 0, "Fields": "not_a_list"}
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_message(message)
        assert ValidationError.INVALID_ELEMENT_FORMAT == exc_info.value.error_code

    def test_validate_field_value_types(self, validator):
        """Test validation of field value types"""
        message = {
            "Name": "test_message",
            "SIN": 16,
            "MIN": 1,
            "Fields": [{"Name": "int_field", "Type": "unsignedint", "Value": "not_an_int"}],
        }
        with pytest.raises(ValidationError):
            validator.validate_message(message)

    def test_validate_array_field_structure(self, validator):
        """Test validation of array field structure"""
        message = {
            "Name": "test_message",
            "SIN": 16,
            "MIN": 1,
            "Fields": [
                {
                    "Name": "array_field",
                    "Type": "array",
                    "Elements": "not_a_list",  # Invalid Elements type
                }
            ],
        }
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_message(message)
        assert ValidationError.INVALID_FIELD_FORMAT == exc_info.value.error_code

        # Test missing Elements in array field
        message["Fields"][0] = {
            "Name": "array_field",
            "Type": "array",
        }
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_message(message)
        assert ValidationError.MISSING_REQUIRED_FIELD == exc_info.value.error_code

    def test_validate_field_required_properties(self, validator):
        """Test validation of required field properties"""
        # Test missing Name
        message = {
            "Name": "test_message",
            "SIN": 16,
            "MIN": 1,
            "Fields": [{"Type": "string", "Value": "test"}],  # Missing Name
        }
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_message(message)
        assert exc_info.value.error_code == ValidationError.MISSING_REQUIRED_FIELD
        assert "Name" in str(exc_info.value)

        # Test missing Type
        message["Fields"][0] = {"Name": "field1", "Value": "test"}
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_message(message)
        assert exc_info.value.error_code == ValidationError.MISSING_REQUIRED_FIELD
        assert "Type" in str(exc_info.value)

        # Test missing Value (except for array fields)
        message["Fields"][0] = {"Name": "field1", "Type": "string"}
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_message(message)
        assert exc_info.value.error_code == ValidationError.MISSING_REQUIRED_FIELD
        assert "Value" in str(exc_info.value)

        # Test array field with missing Elements
        message["Fields"][0] = {"Name": "field1", "Type": "array"}
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_message(message)
        assert exc_info.value.error_code == ValidationError.MISSING_REQUIRED_FIELD
        assert "Elements" in str(exc_info.value)

    def test_validate_dynamic_field(self, validator):
        """Test validation of dynamic field type"""
        message = {
            "Name": "test_message",
            "SIN": 16,
            "MIN": 1,
            "Fields": [
                {
                    "Name": "dynamic_field",
                    "Type": "dynamic",
                    "Value": "test",
                    "TypeAttribute": "string",
                }
            ],
        }
        validator.validate_message(message)  # Should not raise

        # Test missing TypeAttribute
        message["Fields"][0]["TypeAttribute"] = None
        with pytest.raises(ValidationError):
            validator.validate_message(message)

        # Test invalid TypeAttribute
        message["Fields"][0]["TypeAttribute"] = "invalid_type"
        with pytest.raises(ValidationError):
            validator.validate_message(message)

    def test_validate_message_name_type(self):
        """Test validation of message name type"""
        validator = OGxMessageValidator()
        message = {
            "Name": 42,  # Invalid: number instead of string
            "SIN": 16,
            "MIN": 1,
            "Fields": [],
        }

        with pytest.raises(ValidationError) as exc_info:
            validator.validate_message(message)
        assert exc_info.value.error_code == ValidationError.INVALID_FIELD_VALUE
        assert "Name must be a string" in str(exc_info.value)
