"""Tests for OGx protocol message structure and validation"""

import pytest

from src.protocols.ogx.constants import FieldType
from src.protocols.ogx.exceptions import ValidationError
from src.protocols.ogx.models.fields import ArrayField, Element, Field
from src.protocols.ogx.models.messages import OGxMessage
from src.protocols.ogx.validation.message_validator import OGxMessageValidator


class TestMessage:
    """Test suite for OGx message functionality.

    Tests basic message operations, initialization, validation, and serialization
    according to the N214 specification.
    """

    @pytest.fixture
    def validator(self):
        """Create a message validator instance for testing"""
        return OGxMessageValidator()

    def test_message_initialization(self):
        """Test basic message initialization with valid fields"""
        fields = [
            Field(name="field1", type=FieldType.STRING, value="test"),
            Field(name="field2", type=FieldType.UNSIGNED_INT, value=42),
        ]
        message = OGxMessage(
            name="test_message", sin=16, min=1, fields=fields  # Example SIN  # Example MIN
        )

        assert message.name == "test_message"
        assert message.sin == 16
        assert message.min == 1
        assert len(message.fields) == 2

    def test_message_from_dict_simple(self):
        """Test creating message from dictionary with simple fields"""
        data = {
            "Name": "test_message",
            "SIN": 16,
            "MIN": 1,
            "Fields": [
                {"Name": "field1", "Type": "string", "Value": "test"},
                {"Name": "field2", "Type": "unsignedint", "Value": 42},
            ],
        }
        message = OGxMessage.from_dict(data)

        assert message.name == "test_message"
        assert message.sin == 16
        assert message.min == 1
        assert len(message.fields) == 2
        assert isinstance(message.fields[0], Field)
        assert message.fields[0].name == "field1"
        assert message.fields[0].type == FieldType.STRING
        assert message.fields[0].value == "test"

    def test_message_from_dict_array(self):
        """Test creating message from dictionary with array fields"""
        data = {
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
                        },
                        {
                            "Index": 1,
                            "Fields": [{"Name": "sub_field", "Type": "boolean", "Value": True}],
                        },
                    ],
                }
            ],
        }
        message = OGxMessage.from_dict(data)

        assert message.name == "test_message"
        assert message.sin == 16
        assert message.min == 1
        assert len(message.fields) == 1
        assert isinstance(message.fields[0], ArrayField)
        assert message.fields[0].name == "array_field"
        assert message.fields[0].type == FieldType.ARRAY
        assert len(message.fields[0].elements) == 2
        assert message.fields[0].elements[0].index == 0
        assert message.fields[0].elements[1].index == 1

    def test_message_from_dict_empty_fields(self):
        """Test creating message from dictionary with empty fields"""
        data = {
            "Name": "test_message",
            "SIN": 16,
            "MIN": 1,
            "Fields": [],
        }
        message = OGxMessage.from_dict(data)

        assert message.name == "test_message"
        assert message.sin == 16
        assert message.min == 1
        assert len(message.fields) == 0

    def test_message_from_dict_array_empty_elements(self):
        """Test creating message from dictionary with array field having empty elements"""
        data = {
            "Name": "test_message",
            "SIN": 16,
            "MIN": 1,
            "Fields": [
                {
                    "Name": "array_field",
                    "Type": "array",
                    "Elements": [],
                }
            ],
        }
        message = OGxMessage.from_dict(data)

        assert message.name == "test_message"
        assert len(message.fields) == 1
        assert isinstance(message.fields[0], ArrayField)
        assert len(message.fields[0].elements) == 0

    def test_message_to_dict_array(self):
        """Test message serialization to dictionary with array fields"""
        elements = [
            Element(
                index=0,
                fields=[Field(name="sub_field", type=FieldType.STRING, value="test")],
            ),
            Element(
                index=1,
                fields=[Field(name="sub_field", type=FieldType.BOOLEAN, value=True)],
            ),
        ]
        fields = [ArrayField(name="array_field", type=FieldType.ARRAY, elements=elements)]
        message = OGxMessage(name="test_message", sin=16, min=1, fields=fields)

        dict_repr = message.to_dict()
        assert dict_repr["Name"] == "test_message"
        assert dict_repr["SIN"] == 16
        assert dict_repr["MIN"] == 1
        assert len(dict_repr["Fields"]) == 1
        assert dict_repr["Fields"][0]["Type"] == "array"
        assert len(dict_repr["Fields"][0]["Elements"]) == 2

    def test_message_validation_with_array(self, validator):
        """Test message validation with array fields"""
        elements = [
            Element(
                index=0,
                fields=[
                    Field(name="sub_field", type=FieldType.STRING, value=123)
                ],  # Invalid value type
            ),
        ]
        fields = [ArrayField(name="array_field", type=FieldType.ARRAY, elements=elements)]
        message = OGxMessage(name="test_message", sin=16, min=1, fields=fields)

        with pytest.raises(ValidationError):
            validator.validate_message(message.to_dict())

    def test_message_validation_empty(self, validator):
        """Test message validation with no fields"""
        message = OGxMessage(name="test_message", sin=16, min=1, fields=[])
        validator.validate_message(message.to_dict())  # Should not raise

    def test_message_validation_duplicate_fields(self, validator):
        """Test message validation with duplicate field names"""
        fields = [
            Field(name="same_name", type=FieldType.STRING, value="test1"),
            Field(name="same_name", type=FieldType.STRING, value="test2"),
        ]
        message = OGxMessage(name="test_message", sin=16, min=1, fields=fields)

        with pytest.raises(ValidationError) as exc_info:
            validator.validate_message(message.to_dict())
        assert "Duplicate field name" in str(exc_info.value)

    def test_message_to_dict(self):
        """Test message serialization to dictionary format"""
        fields = [
            Field(name="field1", type=FieldType.STRING, value="test"),
            Field(name="field2", type=FieldType.UNSIGNED_INT, value=42),
        ]
        message = OGxMessage(name="test_message", sin=16, min=1, fields=fields)

        dict_repr = message.to_dict()
        assert dict_repr["Name"] == "test_message"
        assert dict_repr["SIN"] == 16
        assert dict_repr["MIN"] == 1
        assert len(dict_repr["Fields"]) == 2
        assert dict_repr["Fields"][0]["Name"] == "field1"
        assert dict_repr["Fields"][1]["Name"] == "field2"

    def test_message_field_validation(self):
        """Test validation of message fields"""
        # Create a message with an invalid field
        fields = [
            Field(
                name="field1", type=FieldType.STRING, value=42
            ),  # Invalid: number for string field
        ]
        message = OGxMessage(name="test_message", sin=16, min=1, fields=fields)

        # Validation should fail
        with pytest.raises(ValidationError):
            message.validate()

        # Create a message with multiple fields, one invalid
        fields = [
            Field(name="field1", type=FieldType.STRING, value="test"),  # Valid
            Field(name="field2", type=FieldType.UNSIGNED_INT, value=-1),  # Invalid: negative number
        ]
        message = OGxMessage(name="test_message", sin=16, min=1, fields=fields)

        # Validation should fail
        with pytest.raises(ValidationError):
            message.validate()


class TestCommonMessage:
    """Test suite for OGx common message functionality.

    Tests common message operations, validation, and error handling
    according to the N214 specification.
    """

    @pytest.fixture
    def validator(self):
        """Create a message validator instance for testing"""
        return OGxMessageValidator()

    def test_common_message_initialization(self):
        """Test common message initialization with valid fields"""
        fields = [
            Field(name="field1", type=FieldType.STRING, value="test"),
            Field(name="field2", type=FieldType.UNSIGNED_INT, value=42),
        ]
        message = OGxMessage(name="test_message", sin=16, min=1, fields=fields)

        assert message.name == "test_message"
        assert message.sin == 16
        assert message.min == 1
        assert len(message.fields) == 2

    def test_common_message_to_dict(self):
        """Test common message serialization to dictionary format"""
        fields = [
            Field(name="field1", type=FieldType.STRING, value="test"),
            Field(name="field2", type=FieldType.UNSIGNED_INT, value=42),
        ]
        message = OGxMessage(name="test_message", sin=16, min=1, fields=fields)

        dict_repr = message.to_dict()
        assert dict_repr["Name"] == "test_message"
        assert dict_repr["SIN"] == 16
        assert dict_repr["MIN"] == 1
        assert len(dict_repr["Fields"]) == 2

    def test_common_message_validation(self, validator):
        """Test common message validation and error handling"""
        # Test with invalid SIN
        message = OGxMessage(
            name="test_message",
            sin=-1,  # Invalid negative SIN
            min=1,
            fields=[],
        )
        with pytest.raises(ValidationError):
            validator.validate_message(message.to_dict())

        # Test with invalid MIN
        message = OGxMessage(
            name="test_message",
            sin=16,
            min=-1,  # Invalid negative MIN
            fields=[],
        )
        with pytest.raises(ValidationError):
            validator.validate_message(message.to_dict())

        # Test with missing name
        message = OGxMessage(name="", sin=16, min=1, fields=[])  # Empty name
        with pytest.raises(ValidationError):
            validator.validate_message(message.to_dict())
