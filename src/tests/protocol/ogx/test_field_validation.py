"""Tests for OGx field validation edge cases"""

from base64 import b64encode

import pytest

from protocols.ogx.validation.json.field_validator import OGxFieldValidator
from src.protocols.ogx.constants import FieldType
from src.protocols.ogx.exceptions import ValidationError
from src.protocols.ogx.models.fields import (
    ArrayField,
    DynamicField,
    Element,
    Field,
    PropertyField,
)


class TestField:
    """Test cases for field validation"""

    @pytest.fixture
    def validator(self) -> OGxFieldValidator:
        """Create a field validator instance"""
        return OGxFieldValidator()

    def test_boolean_field_validation(self):
        """Test validation of boolean field values"""
        # Valid boolean field
        field = Field(name="test_bool", type=FieldType.BOOLEAN, value=True)
        field.validate()  # Should not raise

        # Invalid boolean field
        field = Field(name="test_bool", type=FieldType.BOOLEAN, value="true")
        with pytest.raises(ValidationError):
            field.validate()

    def test_unsigned_int_field_validation(self):
        """Test validation of unsigned integer field values"""
        # Valid unsigned int
        field = Field(name="test_uint", type=FieldType.UNSIGNED_INT, value=42)
        field.validate()  # Should not raise

        # Invalid: negative number
        field = Field(name="test_uint", type=FieldType.UNSIGNED_INT, value=-1)
        with pytest.raises(ValidationError):
            field.validate()

        # Invalid: non-integer
        field = Field(name="test_uint", type=FieldType.UNSIGNED_INT, value="abc")
        with pytest.raises(ValidationError):
            field.validate()

    def test_signed_int_field_validation(self):
        """Test validation of signed integer field values"""
        # Valid signed ints
        field = Field(name="test_int", type=FieldType.SIGNED_INT, value=42)
        field.validate()
        field = Field(name="test_int", type=FieldType.SIGNED_INT, value=-42)
        field.validate()

        # Invalid: non-integer
        field = Field(name="test_int", type=FieldType.SIGNED_INT, value="abc")
        with pytest.raises(ValidationError):
            field.validate()

    def test_string_field_validation(self):
        """Test validation of string field values"""
        # Valid string
        field = Field(name="test_str", type=FieldType.STRING, value="test")
        field.validate()

        # Invalid: non-string
        field = Field(name="test_str", type=FieldType.STRING, value=42)
        with pytest.raises(ValidationError):
            field.validate()

    def test_enum_field_validation(self):
        """Test validation of enum field values"""
        # Valid enum string
        field = Field(name="test_enum", type=FieldType.ENUM, value="OPTION_A")
        field.validate()

        # Invalid: non-string
        field = Field(name="test_enum", type=FieldType.ENUM, value=42)
        with pytest.raises(ValidationError):
            field.validate()

    def test_data_field_validation(self):
        """Test validation of data field values"""
        # Valid base64 string
        valid_b64 = b64encode(b"test data").decode()
        field = Field(name="test_data", type=FieldType.DATA, value=valid_b64)
        field.validate()

        # Valid bytes
        field = Field(name="test_data", type=FieldType.DATA, value=b"test data")
        field.validate()

        # Invalid: not base64 or bytes
        field = Field(name="test_data", type=FieldType.DATA, value="not base64!")
        with pytest.raises(ValidationError):
            field.validate()


class TestArrayField:
    """Test cases for array field validation"""

    def test_array_field_initialization(self):
        """Test array field initialization"""
        elements = [
            Element(index=0, fields=[Field(name="sub_field", type=FieldType.STRING, value="test")])
        ]
        array_field = ArrayField(name="test_array", type=FieldType.ARRAY, elements=elements)

        assert array_field.type == FieldType.ARRAY
        assert array_field.value is None
        assert len(array_field.elements) == 1

    def test_array_field_to_dict(self):
        """Test array field serialization to dictionary"""
        elements = [
            Element(index=0, fields=[Field(name="sub_field", type=FieldType.STRING, value="test")])
        ]
        array_field = ArrayField(name="test_array", type=FieldType.ARRAY, elements=elements)

        dict_repr = array_field.to_dict()
        assert dict_repr["Name"] == "test_array"
        assert dict_repr["Type"] == FieldType.ARRAY.value
        assert len(dict_repr["Elements"]) == 1
        assert dict_repr["Elements"][0]["Index"] == 0


class TestDynamicField:
    """Test cases for dynamic field validation"""

    def test_dynamic_field_initialization(self):
        """Test dynamic field initialization"""
        field = DynamicField(
            name="test_dynamic",
            type=FieldType.DYNAMIC,
            value="test",
            type_attribute=FieldType.STRING.value,
        )
        assert field.type == FieldType.DYNAMIC
        assert field.type_attribute == FieldType.STRING.value

    def test_dynamic_field_to_dict(self):
        """Test dynamic field serialization to dictionary"""
        field = DynamicField(
            name="test_dynamic",
            type=FieldType.DYNAMIC,
            value="test",
            type_attribute=FieldType.STRING.value,
        )
        dict_repr = field.to_dict()
        assert dict_repr["Name"] == "test_dynamic"
        assert dict_repr["Type"] == FieldType.STRING.value
        assert dict_repr["Value"] == "test"


class TestPropertyField:
    """Test cases for property field validation"""

    def test_property_field_initialization(self):
        """Test property field initialization"""
        field = PropertyField(
            name="test_property",
            type=FieldType.PROPERTY,
            value="test",
            type_attribute=FieldType.STRING.value,
        )
        assert field.type == FieldType.PROPERTY
        assert field.type_attribute == FieldType.STRING.value

    def test_property_field_to_dict(self):
        """Test property field serialization to dictionary"""
        field = PropertyField(
            name="test_property",
            type=FieldType.PROPERTY,
            value="test",
            type_attribute=FieldType.STRING.value,
        )
        dict_repr = field.to_dict()
        assert dict_repr["Name"] == "test_property"
        assert dict_repr["Type"] == FieldType.STRING.value
        assert dict_repr["Value"] == "test"


class TestFieldValidator:
    """Test cases for OGxFieldValidator"""

    @pytest.fixture
    def validator(self) -> OGxFieldValidator:
        """Create a field validator instance"""
        return OGxFieldValidator()

    def test_validate_field_value_dynamic(self, validator):
        """Test validation of dynamic field values"""
        # Valid dynamic field with string type
        validator.validate_field_value(FieldType.DYNAMIC, "test", "string")

        # Invalid: missing type attribute
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_field_value(FieldType.DYNAMIC, "test")
        assert exc_info.value.error_code == ValidationError.INVALID_FIELD_TYPE

        # Invalid: unknown type attribute
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_field_value(FieldType.DYNAMIC, "test", "unknown")
        assert exc_info.value.error_code == ValidationError.INVALID_FIELD_TYPE

    def test_validate_field_value_property(self, validator):
        """Test validation of property field values"""
        # Valid property field with string type
        validator.validate_field_value(FieldType.PROPERTY, "test", "string")

        # Invalid: missing type attribute
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_field_value(FieldType.PROPERTY, "test")
        assert exc_info.value.error_code == ValidationError.INVALID_FIELD_TYPE

    def test_validate_message_size(self, validator):
        """Test validation of message size limits"""
        # Valid small message
        validator.validate_message_size(b"x" * 50, "small")

        # Invalid small message
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_message_size(b"x" * 101, "small")
        assert exc_info.value.error_code == ValidationError.INVALID_MESSAGE_FORMAT

        # Valid regular message
        validator.validate_message_size(b"x" * 1500, "regular")

        # Invalid regular message
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_message_size(b"x" * 2001, "regular")
        assert exc_info.value.error_code == ValidationError.INVALID_MESSAGE_FORMAT

        # Valid large message
        validator.validate_message_size(b"x" * 8000, "large")

        # Invalid large message
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_message_size(b"x" * 10001, "large")
        assert exc_info.value.error_code == ValidationError.INVALID_MESSAGE_FORMAT

    def test_validate_terminal_id(self, validator):
        """Test validation of terminal ID format"""
        # Valid terminal ID
        validator.validate_terminal_id("0123456789AB")

        # Invalid terminal ID - wrong length
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_terminal_id("0123456789")
        assert exc_info.value.error_code == ValidationError.INVALID_FIELD_FORMAT

        # Invalid terminal ID - non-hex characters
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_terminal_id("0123456789GZ")
        assert exc_info.value.error_code == ValidationError.INVALID_FIELD_FORMAT

    def test_validate_mac_address(self, validator):
        """Test validation of MAC address format"""
        # Valid MAC address
        validator.validate_mac_address("00:11:22:33:44:55")

        # Invalid MAC address - wrong format
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_mac_address("00-11-22-33-44-55")
        assert exc_info.value.error_code == ValidationError.INVALID_FIELD_FORMAT

        # Invalid MAC address - non-hex characters
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_mac_address("GG:11:22:33:44:55")
        assert exc_info.value.error_code == ValidationError.INVALID_FIELD_FORMAT

    def test_validate_satellite_network(self, validator):
        """Test validation of satellite network value"""
        # Valid network values
        validator.validate_satellite_network(0)  # IsatData Pro
        validator.validate_satellite_network(1)  # OGx

        # Invalid network value
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_satellite_network(2)
        assert exc_info.value.error_code == ValidationError.INVALID_FIELD_VALUE

    def test_validate_base64(self, validator):
        """Test validation of base64 encoding"""
        # Valid base64
        valid_b64 = "SGVsbG8gV29ybGQ="  # "Hello World"
        validator.validate_base64(valid_b64)

        # Invalid base64 - incorrect padding
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_base64("SGVsbG8gV29ybGQ")
        assert exc_info.value.error_code == ValidationError.INVALID_FIELD_FORMAT

        # Invalid base64 - invalid characters
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_base64("!@#$%^&*")
        assert exc_info.value.error_code == ValidationError.INVALID_FIELD_FORMAT

    def test_validate_timestamp(self, validator):
        """Test validation of UTC timestamp format"""
        # Valid timestamp
        validator.validate_timestamp("2024-02-05 12:34:56")

        # Invalid timestamp - wrong format
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_timestamp("2024/02/05 12:34:56")
        assert exc_info.value.error_code == ValidationError.INVALID_FIELD_FORMAT

        # Invalid timestamp - invalid date
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_timestamp("2024-13-45 12:34:56")
        assert exc_info.value.error_code == ValidationError.INVALID_FIELD_FORMAT

        # Invalid timestamp - invalid time
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_timestamp("2024-02-05 25:61:99")
        assert exc_info.value.error_code == ValidationError.INVALID_FIELD_FORMAT

    def test_validate_message_name(self, validator):
        """Test validation of message name format"""
        # Valid message name
        validator.validate_message_name("TestMessage")

        # Empty message name
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_message_name("")
        assert exc_info.value.error_code == ValidationError.INVALID_FIELD_FORMAT

    def test_validate_array_field_value(self, validator):
        """Test validation of array field values"""
        # Valid array - None value
        validator.validate_field_value(FieldType.ARRAY, None)

        # Valid array - list value
        validator.validate_field_value(FieldType.ARRAY, [])

        # Invalid array - not a list
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_field_value(FieldType.ARRAY, "not a list")
        assert exc_info.value.error_code == ValidationError.INVALID_FIELD_VALUE

    def test_validate_message_field_value(self, validator):
        """Test validation of message field values"""
        # Valid message - None value
        validator.validate_field_value(FieldType.MESSAGE, None)

        # Valid message - dict value
        validator.validate_field_value(FieldType.MESSAGE, {})

        # Invalid message - not a dict
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_field_value(FieldType.MESSAGE, "not a dict")
        assert exc_info.value.error_code == ValidationError.INVALID_FIELD_VALUE

    def test_validate_unknown_field_type(self, validator):
        """Test validation with unknown field type"""
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_field_value("unknown_type", "value")
        assert exc_info.value.error_code == ValidationError.INVALID_FIELD_TYPE

    def test_validate_field_value_type_conversions(self, validator):
        """Test field value type conversions"""
        # Test type conversion for unsigned int
        validator.validate_field_value(FieldType.UNSIGNED_INT, "42")  # String to int
        validator.validate_field_value(FieldType.UNSIGNED_INT, 42.0)  # Float to int

        # Test type conversion for signed int
        validator.validate_field_value(FieldType.SIGNED_INT, "-42")  # String to int
        validator.validate_field_value(FieldType.SIGNED_INT, -42.0)  # Float to int

        # Test invalid type conversions
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_field_value(FieldType.UNSIGNED_INT, "not a number")
        assert exc_info.value.error_code == ValidationError.INVALID_FIELD_VALUE

        with pytest.raises(ValidationError) as exc_info:
            validator.validate_field_value(FieldType.SIGNED_INT, "not a number")
        assert exc_info.value.error_code == ValidationError.INVALID_FIELD_VALUE

    def test_validate_base64_error_handling(self, validator):
        """Test base64 validation error handling"""
        # Test invalid base64 with non-base64 characters
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_base64("!@#$%^&*")
        assert exc_info.value.error_code == ValidationError.INVALID_FIELD_FORMAT

        # Test invalid base64 with incorrect padding
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_base64("SGVsbG8=====")  # Too much padding
        assert exc_info.value.error_code == ValidationError.INVALID_FIELD_FORMAT

        # Test invalid base64 that can't be decoded
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_base64("A")  # Single character is not valid base64
        assert exc_info.value.error_code == ValidationError.INVALID_FIELD_FORMAT

        # Test base64 that decodes but can't be re-encoded to the same value
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_base64("YWJjZA=")  # Valid base64 but wrong padding
        assert exc_info.value.error_code == ValidationError.INVALID_FIELD_FORMAT

    def test_validate_message_name_special_cases(self, validator):
        """Test message name validation special cases"""
        # Test empty message name
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_message_name("")
        assert exc_info.value.error_code == ValidationError.INVALID_FIELD_FORMAT

        # Test message name with spaces
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_message_name("Invalid Message")
        assert exc_info.value.error_code == ValidationError.INVALID_FIELD_FORMAT

        # Test message name with special characters
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_message_name("Invalid@Message")
        assert exc_info.value.error_code == ValidationError.INVALID_FIELD_FORMAT

        # Test valid message names with numbers and underscores
        validator.validate_message_name("12345")  # Numbers only is valid
        validator.validate_message_name("Message_123")  # Mixed alphanumeric with underscore
        validator.validate_message_name("_123_test")  # Starting with underscore

    def test_validate_field_value_error_handling(self, validator):
        """Test field value validation error handling"""
        # Test TypeError handling
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_field_value(FieldType.BOOLEAN, None)
        assert exc_info.value.error_code == ValidationError.INVALID_FIELD_VALUE

        # Test ValueError handling
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_field_value(FieldType.UNSIGNED_INT, -1)
        assert exc_info.value.error_code == ValidationError.INVALID_FIELD_VALUE

        # Test unknown field type
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_field_value("invalid_type", "value")
        assert exc_info.value.error_code == ValidationError.INVALID_FIELD_TYPE

    def test_validate_sin_min(self, validator):
        """Test validation of SIN and MIN values"""
        # Valid SIN and MIN
        validator.validate_sin_min(16, 1)

        # Invalid SIN - negative
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_sin_min(-1, 1)
        assert exc_info.value.error_code == ValidationError.INVALID_FIELD_VALUE
        assert "SIN must be a non-negative integer" in str(exc_info.value)

        # Invalid MIN - negative
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_sin_min(16, -1)
        assert exc_info.value.error_code == ValidationError.INVALID_FIELD_VALUE
        assert "MIN must be a non-negative integer" in str(exc_info.value)

        # Invalid SIN - wrong type
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_sin_min("16", 1)
        assert exc_info.value.error_code == ValidationError.INVALID_FIELD_VALUE
        assert "SIN must be a non-negative integer" in str(exc_info.value)

        # Invalid MIN - wrong type
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_sin_min(16, "1")
        assert exc_info.value.error_code == ValidationError.INVALID_FIELD_VALUE
        assert "MIN must be a non-negative integer" in str(exc_info.value)

    def test_validate_field_value_error_handling_extended(self, validator):
        """Test extended error handling in field value validation"""
        # Test TypeError in field value validation
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_field_value(FieldType.BOOLEAN, None)
        assert exc_info.value.error_code == ValidationError.INVALID_FIELD_VALUE
        assert "Invalid value for field type" in str(exc_info.value)

        # Test ValueError in field value validation
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_field_value(FieldType.UNSIGNED_INT, -1)
        assert exc_info.value.error_code == ValidationError.INVALID_FIELD_VALUE
        assert "Invalid value for field type" in str(exc_info.value)

        # Test unknown field type
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_field_value("invalid_type", "value")
        assert exc_info.value.error_code == ValidationError.INVALID_FIELD_TYPE
        assert "Unknown field type" in str(exc_info.value)

    def test_validate_field_value_data_type_errors(self):
        """Test validation of data field type errors"""
        validator = OGxFieldValidator()

        # Test invalid data type (not str or bytes)
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_field_value(FieldType.DATA, 42)
        assert exc_info.value.error_code == ValidationError.INVALID_FIELD_VALUE
        assert f"Invalid value for field type {FieldType.DATA}: 42" in str(exc_info.value)

        # Test invalid base64 string
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_field_value(FieldType.DATA, "not-base64!")
        assert exc_info.value.error_code == ValidationError.INVALID_FIELD_FORMAT
        assert "Invalid base64 encoding" in str(exc_info.value)

        # Test invalid base64 string (incorrect padding)
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_field_value(FieldType.DATA, "YWJjZA=")  # Invalid padding
        assert exc_info.value.error_code == ValidationError.INVALID_FIELD_FORMAT
        assert "Invalid base64 encoding" in str(exc_info.value)
