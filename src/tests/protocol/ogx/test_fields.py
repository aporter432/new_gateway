"""Tests for OGx protocol field validation and types"""

from base64 import b64encode
import pytest
from src.protocols.ogx.models.fields import Field, ArrayField, Element, DynamicField, PropertyField
from src.protocols.ogx.constants import FieldType
from src.protocols.ogx.exceptions import ValidationError


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
    """Test cases for array field functionality"""

    def test_array_field_initialization(self):
        """Test array field initialization and structure"""
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
