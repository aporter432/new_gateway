"""Tests for Field model behavior and integration with OGWS-1 validation.

This module tests the Field model's responsibilities:
1. Pydantic model structure and behavior
2. Integration with OGxFieldValidator
3. Serialization according to OGWS-1.txt requirements
"""

import pytest
from pydantic import ValidationError as PydanticValidationError

from protocols.ogx.constants import FieldType
from protocols.ogx.models.fields import Element, Field
from protocols.ogx.validation.common.validation_exceptions import ValidationError


class TestFieldModel:
    """Test Field model behavior and integration."""

    def test_field_structure(self):
        """Test Field model structure and required attributes."""
        # Test required attributes
        field = Field(name="test", type=FieldType.STRING, value="test")
        assert field.name == "test"
        assert field.type == FieldType.STRING
        assert field.value == "test"
        assert field.elements is None
        assert field.message is None

        # Test optional attributes
        field = Field(name="test", type=FieldType.STRING)
        assert field.value is None

    def test_field_serialization(self):
        """Test Field serialization according to OGWS-1.txt requirements.

        Requirements:
        1. Field names must be capitalized
        2. Values must be strings in output
        3. Optional fields should be omitted if None
        """
        field = Field(name="test", type=FieldType.STRING, value="test")
        serialized = field.model_dump(by_alias=True)
        assert serialized == {"Name": "test", "Type": "string", "Value": "test"}  # Capitalized

        # Test value type serialization
        test_cases = [
            (FieldType.BOOLEAN, True, "True"),
            (FieldType.BOOLEAN, False, "False"),
            (FieldType.UNSIGNED_INT, 42, "42"),
            (FieldType.SIGNED_INT, -42, "-42"),
            (FieldType.STRING, "test", "test"),
            (FieldType.ENUM, "ACTIVE", "ACTIVE"),
        ]

        for field_type, value, expected in test_cases:
            field = Field(name="test", type=field_type, value=value)
            serialized = field.model_dump(by_alias=True)
            assert serialized["Value"] == expected
            assert isinstance(serialized["Value"], str)

        # Test None value handling
        field = Field(name="test", type=FieldType.STRING, value=None)
        serialized = field.model_dump(by_alias=True)
        assert "Value" not in serialized

    def test_validator_integration(self):
        """Test integration with OGxFieldValidator.

        The Field model should:
        1. Use OGxFieldValidator for validation
        2. Convert validation errors to Pydantic errors
        3. Handle type conversion where needed
        """
        # Test validation error propagation
        with pytest.raises(PydanticValidationError) as exc_info:
            Field(name="test", type=FieldType.BOOLEAN, value="invalid")
        assert "Value must be a boolean" in str(exc_info.value)

        # Test boolean conversion
        field = Field(name="test", type=FieldType.BOOLEAN, value="true")
        assert field.value is True
        field = Field(name="test", type=FieldType.BOOLEAN, value="false")
        assert field.value is False

        # Test that validation happens on creation
        with pytest.raises(PydanticValidationError):
            Field(name="test", type=FieldType.UNSIGNED_INT, value=-1)

    def test_bytes_handling(self):
        """Test handling of binary data in DATA fields."""
        # Test bytes to base64 conversion
        field = Field(name="test_data", type=FieldType.DATA, value=b"test data")
        serialized = field.model_dump(by_alias=True)
        assert serialized["Value"] == "dGVzdCBkYXRh"  # base64 encoded

        # Test existing base64 preservation
        field = Field(name="test_data", type=FieldType.DATA, value="dGVzdCBkYXRh")
        serialized = field.model_dump(by_alias=True)
        assert serialized["Value"] == "dGVzdCBkYXRh"


class TestArrayFields:
    """Test cases for array field functionality"""

    def test_array_field_initialization(self):
        """Test array field initialization"""
        # Test default initialization
        field = Field(name="test_array", type=FieldType.ARRAY)
        Field.model_validate(field.model_dump())
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
        field = Field(name="test_array", type=FieldType.ARRAY, elements=elements)
        Field.model_validate(field.model_dump())
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
        field = Field(name="test_array", type=FieldType.ARRAY, elements=elements)
        Field.model_validate(field.model_dump())

        dict_repr = field.model_dump(by_alias=True)
        assert dict_repr["Name"] == "test_array"
        assert dict_repr["Type"] == "array"
        assert len(dict_repr["Elements"]) == 1
        assert dict_repr["Elements"][0]["Index"] == 0
        assert dict_repr["Elements"][0]["Fields"][0]["Name"] == "sub_field"


class TestDynamicFields:
    """Test cases for dynamic field functionality"""

    def test_dynamic_field_initialization(self):
        """Test dynamic field initialization and type handling"""
        field = Field(
            name="test_dynamic",
            type=FieldType.DYNAMIC,
            value="test",
            type_attribute=FieldType.STRING.value,
        )
        Field.model_validate(field.model_dump())
        assert field.type == FieldType.DYNAMIC
        assert field.type_attribute == FieldType.STRING.value

    def test_dynamic_field_to_dict(self):
        """Test dynamic field serialization to dictionary"""
        field = Field(
            name="test_dynamic",
            type=FieldType.DYNAMIC,
            value="test",
            type_attribute=FieldType.STRING.value,
        )
        Field.model_validate(field.model_dump())
        dict_repr = field.model_dump(by_alias=True)
        assert dict_repr["Name"] == "test_dynamic"
        assert dict_repr["Type"] == FieldType.STRING.value
        assert dict_repr["Value"] == "test"


class TestPropertyFields:
    """Test cases for property field functionality"""

    def test_property_field_initialization(self):
        """Test property field initialization and type handling"""
        field = Field(
            name="test_property",
            type=FieldType.PROPERTY,
            value="test",
            type_attribute=FieldType.STRING.value,
        )
        Field.model_validate(field.model_dump())
        assert field.type == FieldType.PROPERTY
        assert field.type_attribute == FieldType.STRING.value

    def test_property_field_to_dict(self):
        """Test property field serialization to dictionary"""
        field = Field(
            name="test_property",
            type=FieldType.PROPERTY,
            value="test",
            type_attribute=FieldType.STRING.value,
        )
        Field.model_validate(field.model_dump())
        dict_repr = field.model_dump(by_alias=True)
        assert dict_repr["Name"] == "test_property"
        assert dict_repr["Type"] == FieldType.STRING.value
        assert dict_repr["Value"] == "test"
