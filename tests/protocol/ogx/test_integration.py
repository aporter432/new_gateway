"""Integration tests for OGx protocol functionality"""

import pytest

from protocols.ogx.constants import FieldType
from protocols.ogx.encoding.json.json_codec import OGxJsonCodec
from protocols.ogx.validation.json.message_validator import OGxMessageValidator
from src.protocols.ogx.exceptions import EncodingError, ValidationError
from src.protocols.ogx.models.fields import ArrayField, Element, Field
from src.protocols.ogx.models.messages import OGxMessage


class TestOGxProtocolIntegration:
    """Test suite for OGx protocol integration testing"""

    @pytest.fixture
    def validator(self):
        """Create a message validator instance"""
        return OGxMessageValidator()

    @pytest.fixture
    def codec(self):
        """Create a JSON codec instance"""
        return OGxJsonCodec()

    def test_complete_message_lifecycle(self, validator, codec):
        """Test complete message lifecycle: create -> validate -> encode -> decode -> validate"""
        # Create a complex message with various field types
        fields = [
            Field(name="string_field", type=FieldType.STRING, value="test"),
            Field(name="int_field", type=FieldType.SIGNED_INT, value=-42),
            ArrayField(
                name="array_field",
                type=FieldType.ARRAY,
                elements=[
                    Element(
                        index=0,
                        fields=[Field(name="sub_field", type=FieldType.BOOLEAN, value=True)],
                    )
                ],
            ),
        ]

        original_message = OGxMessage(name="test_message", sin=16, min=1, fields=fields)

        # Step 1: Initial validation
        dict_message = original_message.to_dict()
        validator.validate_message(dict_message)

        # Step 2: Encode to JSON
        json_str = codec.encode(original_message)

        # Step 3: Decode from JSON
        decoded_message = codec.decode(json_str)

        # Step 4: Validate decoded message
        dict_message = decoded_message.to_dict()
        validator.validate_message(dict_message)

        # Step 5: Verify content equality
        assert decoded_message.name == original_message.name
        assert decoded_message.sin == original_message.sin
        assert decoded_message.min == original_message.min
        assert len(decoded_message.fields) == len(original_message.fields)

    def test_error_propagation(self, validator, codec):
        """Test error handling and propagation through the stack"""
        # Create an invalid message (missing required fields)
        invalid_message = {
            "Name": "test_message",
            # Missing SIN and MIN
            "Fields": [],
        }

        # Test validation error propagation
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_message(invalid_message)
        assert exc_info.value.error_code == ValidationError.MISSING_REQUIRED_FIELD

        # Test encoding error propagation
        class InvalidMessage:
            """Test class for invalid message scenarios"""

            def to_dict(self):
                """Simulate a message that fails during serialization.

                Raises:
                    ValueError: Always raises to simulate serialization failure.
                """
                raise ValueError("Invalid message")

        with pytest.raises(EncodingError):
            codec.encode(InvalidMessage())

        # Test decoding error propagation
        with pytest.raises(EncodingError):
            codec.decode("invalid json")

    def test_complex_nested_structure(self):
        """Test handling of complex nested message structures"""
        # Create a message with multiple levels of nesting
        nested_fields = [
            ArrayField(
                name="level1",
                type=FieldType.ARRAY,
                elements=[
                    Element(
                        index=0,
                        fields=[
                            Field(name="field1", type=FieldType.STRING, value="test"),
                            ArrayField(
                                name="level2",
                                type=FieldType.ARRAY,
                                elements=[
                                    Element(
                                        index=0,
                                        fields=[
                                            Field(
                                                name="field2", type=FieldType.BOOLEAN, value=True
                                            ),
                                            ArrayField(
                                                name="level3",
                                                type=FieldType.ARRAY,
                                                elements=[
                                                    Element(
                                                        index=0,
                                                        fields=[
                                                            Field(
                                                                name="field3",
                                                                type=FieldType.UNSIGNED_INT,
                                                                value=42,
                                                            )
                                                        ],
                                                    )
                                                ],
                                            ),
                                        ],
                                    )
                                ],
                            ),
                        ],
                    )
                ],
            )
        ]

        message = OGxMessage(name="nested_test", sin=16, min=1, fields=nested_fields)

        # Verify structure is preserved
        assert len(message.fields) == 1
        assert isinstance(message.fields[0], ArrayField)
        assert len(message.fields[0].elements) == 1
        assert len(message.fields[0].elements[0].fields) == 2

    def test_field_type_conversion(self, codec):
        """Test field type conversion and preservation through encode/decode cycle"""
        # Create fields with different types and edge case values
        fields = [
            Field(name="max_uint", type=FieldType.UNSIGNED_INT, value=2**32 - 1),
            Field(name="min_int", type=FieldType.SIGNED_INT, value=-(2**31)),
            Field(name="bool_field", type=FieldType.BOOLEAN, value=True),
            Field(name="empty_string", type=FieldType.STRING, value=""),
            Field(name="unicode_string", type=FieldType.STRING, value="Hello 世界 🌍"),
            Field(name="enum_field", type=FieldType.ENUM, value="OPTION_A"),
        ]

        message = OGxMessage(name="type_test", sin=16, min=1, fields=fields)

        # Encode and decode
        json_str = codec.encode(message)
        decoded = codec.decode(json_str)

        # Verify type and value preservation
        for original, decoded_field in zip(message.fields, decoded.fields):
            assert decoded_field.type == original.type
            assert decoded_field.value == original.value
            assert isinstance(decoded_field.value, type(original.value))

    def test_validation_codec_interaction(self, validator):
        """Test interaction between validation and codec components"""
        # Test that validation errors are caught before encoding
        invalid_message = OGxMessage(
            name="invalid", sin=-1, min=1, fields=[]
        )  # Invalid negative SIN

        with pytest.raises(ValidationError):
            dict_message = invalid_message.to_dict()
            validator.validate_message(dict_message)

        # Test that decoded messages are always valid
        valid_message = {
            "Name": "valid",
            "SIN": 16,
            "MIN": 1,
            "Fields": [{"Name": "field1", "Type": "string", "Value": "test"}],
        }

        # Should not raise any errors
        validator.validate_message(valid_message)
        message_obj = OGxMessage.from_dict(valid_message)
        assert isinstance(message_obj, OGxMessage)
