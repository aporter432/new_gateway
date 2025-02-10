"""Test field implementations according to OGWS-1.txt Section 5 and Table 3."""

import base64
from typing import Any, Dict

import pytest
from pydantic import ValidationError

from protocols.ogx.constants import FieldType
from protocols.ogx.models import Element, Field, Message


@pytest.fixture
def valid_field_data() -> Dict[str, Any]:
    """Provide test field data conforming to OGWS-1.txt field specifications."""
    return {
        "name": "test_field",
        "type": FieldType.STRING,
        "value": "test_value",
    }


class TestFieldTypes:
    """Test field types as defined in OGWS-1.txt Table 3."""

    def test_enum_field(self):
        """Test ENUM field with enumeration value."""
        field = Field(name="status", type=FieldType.ENUM, value="ACTIVE")
        assert field.value == "ACTIVE"
        assert field.dict()["Value"] == "ACTIVE"

    def test_boolean_field(self):
        """Test BOOLEAN field with True/False value."""
        field = Field(name="enabled", type=FieldType.BOOLEAN, value=True)
        assert field.value is True
        assert field.dict()["Value"] == "True"  # Must be string per OGWS-1.txt

    def test_unsigned_int_field(self):
        """Test UNSIGNED_INT field with decimal number."""
        field = Field(name="count", type=FieldType.UNSIGNED_INT, value=42)
        assert field.value == 42
        assert field.dict()["Value"] == "42"  # Must be string per OGWS-1.txt

        with pytest.raises(ValidationError):
            Field(name="count", type=FieldType.UNSIGNED_INT, value=-1)

    def test_signed_int_field(self):
        """Test SIGNED_INT field with decimal number."""
        field = Field(name="temperature", type=FieldType.SIGNED_INT, value=-42)
        assert field.value == -42
        assert field.dict()["Value"] == "-42"  # Must be string per OGWS-1.txt

    def test_string_field(self):
        """Test STRING field with string value."""
        field = Field(name="name", type=FieldType.STRING, value="test")
        assert field.value == "test"
        assert field.dict()["Value"] == "test"

    def test_data_field(self):
        """Test DATA field with base64 encoded data."""
        raw = b"test data"
        b64 = base64.b64encode(raw).decode()
        field = Field(name="payload", type=FieldType.DATA, value=b64)
        assert field.dict()["Value"] == b64

    def test_array_field(self):
        """Test ARRAY field with elements structure."""
        elements = [
            Element(index=0, fields=[Field(name="item", type=FieldType.STRING, value="test")])
        ]
        field = Field(name="list", type=FieldType.ARRAY, elements=elements)
        assert field.elements == elements
        assert "Value" not in field.dict()  # Array type cannot have value

        # Test array validation
        with pytest.raises(ValidationError, match="Array type can only have elements"):
            Field(name="invalid", type=FieldType.ARRAY, value="test")

    def test_message_field(self):
        """Test MESSAGE field with nested message."""
        nested = Message(
            name="status",
            sin=16,
            min=1,
            fields=[Field(name="code", type=FieldType.UNSIGNED_INT, value=200)],
        )
        field = Field(name="response", type=FieldType.MESSAGE, message=nested)
        assert field.message == nested
        assert "Value" not in field.dict()  # Message type cannot have value

        # Test message validation
        with pytest.raises(ValidationError, match="Message type can only have message"):
            Field(name="invalid", type=FieldType.MESSAGE, value="test")
