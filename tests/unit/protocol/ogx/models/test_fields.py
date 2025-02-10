"""Tests for OGx field types and validation"""

import pytest

from protocols.ogx.constants import FieldType
from protocols.ogx.validation.common.validation_exceptions import ValidationError


class TestField:
    """Test cases for basic field types and validation"""

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
        # Valid data field with bytes
        field = Field(name="test_data", type=FieldType.DATA, value=b"test data")
        field.validate()  # Should not raise

        # Valid data field with base64 string
        field = Field(
            name="test_data", type=FieldType.DATA, value="dGVzdCBkYXRh"
        )  # "test data" in base64
        field.validate()  # Should not raise

        # Invalid data field with non-base64 string
        field = Field(name="test_data", type=FieldType.DATA, value="not base64!")
        with pytest.raises(ValidationError):
            field.validate()

        # Invalid data field with wrong type
        field = Field(name="test_data", type=FieldType.DATA, value=123)
        with pytest.raises(ValidationError):
            field.validate()

        # Test None value (should not raise)
        field = Field(name="test_data", type=FieldType.DATA, value=None)
        field.validate()

    def test_field_to_dict_with_bytes(self):
        """Test field serialization with bytes data"""
        # Test DATA field with bytes
        field = Field(name="test_data", type=FieldType.DATA, value=b"test data")
        dict_repr = field.to_dict()
        assert dict_repr["Name"] == "test_data"
        assert dict_repr["Type"] == "data"
        assert dict_repr["Value"] == "dGVzdCBkYXRh"  # base64 encoded "test data"

        # Test field with None value
        field = Field(name="test_null", type=FieldType.STRING, value=None)
        dict_repr = field.to_dict()
        assert dict_repr["Name"] == "test_null"
        assert dict_repr["Type"] == "string"
        assert "Value" not in dict_repr


class TestArrayField:
    """Test cases for array field functionality"""

    def test_array_field_initialization(self):
        """Test array field initialization"""
        # Test default initialization
        field = ArrayField(name="test_array", type=FieldType.ARRAY)
        assert field.type == FieldType.ARRAY
        assert field.value is None
        assert field.elements == []

        # Test initialization with elements
        elements = [
            Element(
                index=0,
                fields=[Field(name="sub_field", type=FieldType.STRING, value="test")],
            )
        ]
        field = ArrayField(name="test_array", type=FieldType.ARRAY, elements=elements)
        assert field.type == FieldType.ARRAY
        assert field.value is None
        assert field.elements == elements

    def test_array_field_to_dict(self):
        """Test array field serialization to dictionary"""
        elements = [
            Element(
                index=0,
                fields=[Field(name="sub_field", type=FieldType.STRING, value="test")],
            )
        ]
        field = ArrayField(name="test_array", type=FieldType.ARRAY, elements=elements)

        dict_repr = field.to_dict()
        assert dict_repr["Name"] == "test_array"
        assert dict_repr["Type"] == "array"
        assert len(dict_repr["Elements"]) == 1
        assert dict_repr["Elements"][0]["Index"] == 0
        assert dict_repr["Elements"][0]["Fields"][0]["Name"] == "sub_field"


class TestDynamicField:
    """Test cases for dynamic field functionality"""

    def test_dynamic_field_initialization(self):
        """Test dynamic field initialization and type handling"""
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
    """Test cases for property field functionality"""

    def test_property_field_initialization(self):
        """Test property field initialization and type handling"""
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
