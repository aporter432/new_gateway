"""Tests for MTWS protocol message models.

This module contains tests that verify the message model implementation
follows the specifications defined in N206 section 2.4.1.
"""

import pytest

from protocols.mtws.constants import (
    FIELD_VALUE_BASE_SIZE,
    MAX_NAME_LENGTH,
    MAX_TYPE_LENGTH,
    MAX_VALUE_LENGTH,
    PROTOCOL_VERSION,
)
from protocols.mtws.exceptions import MTWSElementError, MTWSFieldError
from protocols.mtws.models.messages import (
    CommonMessage,
    CommonMessageElement,
    CommonMessageElementList,
    CommonMessageField,
    FieldValueType,
)


class TestMTWSMessage:
    """Test suite for MTWS message model implementation."""

    def test_create_basic_message(self):
        """Test creation of basic message structure."""
        message = CommonMessage(
            name="test",
            sin=16,
            min_value=1,
            is_forward=False,
            version=PROTOCOL_VERSION,
            fields=[CommonMessageField(name="field1", value="test")],
        )

        assert message.name == "test"
        assert message.sin == 16
        assert message.min_value == 1
        assert not message.is_forward
        assert message.version == PROTOCOL_VERSION
        assert len(message.fields) == 1
        assert message.fields[0].name == "field1"
        assert message.fields[0].value == "test"

    def test_create_message_with_elements(self):
        """Test creation of message with array elements."""
        message = CommonMessage(
            name="getProperties",
            sin=16,
            min_value=8,
            is_forward=False,
            version=PROTOCOL_VERSION,
            fields=[
                CommonMessageField(
                    name="list",
                    elements=CommonMessageElementList(
                        elements=[
                            CommonMessageElement(
                                index=0,
                                fields=[
                                    CommonMessageField(name="sin", value="16"),
                                    CommonMessageField(name="pinList", value="AQID"),
                                ],
                            )
                        ]
                    ),
                )
            ],
        )

        assert message.name == "getProperties"
        assert message.sin == 16
        assert message.min_value == 8
        assert not message.is_forward
        assert len(message.fields) == 1
        assert message.fields[0].name == "list"
        assert isinstance(message.fields[0].elements, CommonMessageElementList)
        assert len(message.fields[0].elements.elements) == 1
        assert message.fields[0].elements.elements[0].index == 0

    def test_message_to_dict(self):
        """Test conversion of message to dictionary format."""
        message = CommonMessage(
            name="test",
            sin=16,
            min_value=1,
            is_forward=False,
            version=PROTOCOL_VERSION,
            fields=[CommonMessageField(name="field1", value="test")],
        )

        dict_form = message.to_dict()
        assert dict_form["Name"] == "test"
        assert dict_form["SIN"] == 16
        assert dict_form["MIN"] == 1
        assert not dict_form["IsForward"]
        assert dict_form["Version"] == PROTOCOL_VERSION
        assert len(dict_form["Fields"]) == 1
        assert dict_form["Fields"][0]["Name"] == "field1"
        assert dict_form["Fields"][0]["Value"] == "test"

    def test_message_from_dict(self):
        """Test creation of message from dictionary format."""
        dict_form = {
            "Name": "test",
            "SIN": 16,
            "MIN": 1,
            "Version": PROTOCOL_VERSION,
            "IsForward": False,
            "Fields": [{"Name": "field1", "Value": "test"}],
        }

        message = CommonMessage.from_dict(dict_form)
        assert message.name == "test"
        assert message.sin == 16
        assert message.min_value == 1
        assert not message.is_forward
        assert message.version == PROTOCOL_VERSION
        assert len(message.fields) == 1
        assert message.fields[0].name == "field1"
        assert message.fields[0].value == "test"

    def test_invalid_message_creation(self):
        """Test handling of invalid message creation attempts."""
        # Missing required fields
        with pytest.raises(MTWSFieldError) as exc_info:
            CommonMessage(
                name=None,  # type: ignore
                sin=None,  # type: ignore
                min_value=None,  # type: ignore
                version=None,  # type: ignore
                is_forward=None,  # type: ignore
            )
        assert exc_info.value.error_code == MTWSFieldError.INVALID_TYPE

        # Invalid SIN value
        with pytest.raises(MTWSFieldError):
            CommonMessage(
                name="test",
                sin=256,  # SIN must be 0-255
                min_value=1,
                is_forward=False,
                version=PROTOCOL_VERSION,
            )

        # Invalid MIN value
        with pytest.raises(MTWSFieldError):
            CommonMessage(
                name="test",
                sin=16,
                min_value=256,  # MIN must be 0-255
                is_forward=False,
                version=PROTOCOL_VERSION,
            )

    def test_complex_message_structure(self):
        """Test handling of complex message structures."""
        message = CommonMessage(
            name="complexTest",
            sin=16,
            min_value=1,
            is_forward=False,
            version=PROTOCOL_VERSION,
            fields=[
                CommonMessageField(
                    name="outer",
                    elements=CommonMessageElementList(
                        elements=[
                            CommonMessageElement(
                                index=0,
                                fields=[
                                    CommonMessageField(
                                        name="inner",
                                        elements=CommonMessageElementList(
                                            elements=[
                                                CommonMessageElement(
                                                    index=0,
                                                    fields=[
                                                        CommonMessageField(
                                                            name="value1", value="test1"
                                                        ),
                                                        CommonMessageField(
                                                            name="value2", value="test2"
                                                        ),
                                                    ],
                                                )
                                            ]
                                        ),
                                    )
                                ],
                            )
                        ]
                    ),
                )
            ],
        )

        assert message.name == "complexTest"
        assert message.sin == 16
        assert message.min_value == 1
        assert not message.is_forward
        assert len(message.fields) == 1
        assert message.fields[0].name == "outer"
        assert isinstance(message.fields[0].elements, CommonMessageElementList)
        assert len(message.fields[0].elements.elements) == 1
        assert message.fields[0].elements.elements[0].index == 0

    def test_message_field_access(self):
        """Test access to message fields."""
        message = CommonMessage(
            name="test",
            sin=16,
            min_value=1,
            is_forward=False,
            version=PROTOCOL_VERSION,
            fields=[
                CommonMessageField(name="field1", value="value1"),
                CommonMessageField(name="field2", value="value2"),
            ],
        )

        assert len(message.fields) == 2
        assert message.fields[0].name == "field1"
        assert message.fields[0].value == "value1"
        assert message.fields[1].name == "field2"
        assert message.fields[1].value == "value2"

    def test_field_value_conversion(self):
        """Test field value type conversion according to N206 section 2.4.1."""
        # Test integer value (with size constraints)
        field = CommonMessageField(name="test", value=123)
        assert field.value == "123"  # Values are converted to strings
        assert len(field.value) + FIELD_VALUE_BASE_SIZE <= MAX_VALUE_LENGTH

        # Test float value (with size constraints)
        field = CommonMessageField(name="test", value=123.45)
        assert field.value == "123.45"
        assert len(field.value) + FIELD_VALUE_BASE_SIZE <= MAX_VALUE_LENGTH

        # Test boolean value (with size constraints)
        field = CommonMessageField(name="test", value=True)
        assert field.value == "True"
        assert len(field.value) + FIELD_VALUE_BASE_SIZE <= MAX_VALUE_LENGTH

        # Test value size limit
        with pytest.raises(MTWSFieldError) as exc_info:
            CommonMessageField(
                name="test", value="x" * (MAX_VALUE_LENGTH - FIELD_VALUE_BASE_SIZE + 1)
            )
        assert exc_info.value.error_code == MTWSFieldError.INVALID_LENGTH

    def test_field_type_validation(self):
        """Test field type validation according to N206 section 2.4.1."""
        # Valid field type
        field = CommonMessageField(
            name="test", field_type=FieldValueType.STRING.value, value="test"
        )
        assert field.type == FieldValueType.STRING.value

        # Invalid field type (not a string)
        with pytest.raises(MTWSFieldError) as exc_info:
            # Using type: ignore to test runtime type checking
            CommonMessageField(name="test", field_type=123, value="test")  # type: ignore
        assert exc_info.value.error_code == MTWSFieldError.INVALID_TYPE

        # Field type too long (>32 chars)
        with pytest.raises(MTWSFieldError) as exc_info:
            CommonMessageField(name="test", field_type="a" * (MAX_TYPE_LENGTH + 1), value="test")
        assert exc_info.value.error_code == MTWSFieldError.INVALID_LENGTH

    def test_message_validation(self):
        """Test message validation according to N206 section 2.4."""
        # Test sequence number validation (16-bit unsigned int)
        message = CommonMessage(
            name="test",
            sin=16,
            min_value=1,
            version=PROTOCOL_VERSION,
            is_forward=False,
            sequence=123,
        )
        assert message.sequence == 123

        # Test invalid sequence number (string)
        with pytest.raises(MTWSFieldError) as exc_info:
            # Using type: ignore to test runtime type checking
            CommonMessage(
                name="test",
                sin=16,
                min_value=1,
                version=PROTOCOL_VERSION,
                is_forward=False,
                sequence="invalid",  # type: ignore
            )
        assert exc_info.value.error_code == MTWSFieldError.INVALID_TYPE

        # Test sequence number out of range (>65535)
        with pytest.raises(MTWSFieldError) as exc_info:
            message = CommonMessage(
                name="test",
                sin=16,
                min_value=1,
                version=PROTOCOL_VERSION,
                is_forward=False,
                sequence=65536,  # Must be <= 65535
            )
        assert exc_info.value.error_code == MTWSFieldError.INVALID_VALUE

        # Test invalid fields type
        with pytest.raises(MTWSFieldError) as exc_info:
            CommonMessage(
                name="test",
                sin=16,
                min_value=1,
                version=PROTOCOL_VERSION,
                is_forward=False,
                fields=[CommonMessageField(name="test")],  # Missing required value
            )
        assert exc_info.value.error_code == MTWSFieldError.MISSING_VALUE

    def test_element_error_handling(self):
        """Test error handling in CommonMessageElement."""
        # Test invalid index type
        with pytest.raises(MTWSElementError) as exc_info:
            CommonMessageElement(
                index="0",  # type: ignore # Should be int
                fields=[CommonMessageField(name="field1", value="test")],
            )
        assert exc_info.value.error_code == MTWSElementError.INVALID_INDEX

        # Test negative index
        with pytest.raises(MTWSElementError) as exc_info:
            CommonMessageElement(
                index=-1,
                fields=[CommonMessageField(name="field1", value="test")],
            )
        assert exc_info.value.error_code == MTWSElementError.NEGATIVE_INDEX

        # Test empty fields
        with pytest.raises(MTWSElementError) as exc_info:
            CommonMessageElement(index=0, fields=[])
        assert exc_info.value.error_code == MTWSElementError.MISSING_FIELDS

        # Test duplicate field names
        with pytest.raises(MTWSElementError) as exc_info:
            CommonMessageElement(
                index=0,
                fields=[
                    CommonMessageField(name="field1", value="test1"),
                    CommonMessageField(name="field1", value="test2"),  # Duplicate name
                ],
            )
        assert exc_info.value.error_code == MTWSElementError.INVALID_FIELDS

    def test_element_list_error_handling(self):
        """Test error handling in CommonMessageElementList."""
        # Test empty elements list
        with pytest.raises(MTWSElementError) as exc_info:
            CommonMessageElementList(elements=[])
        assert exc_info.value.error_code == MTWSElementError.MISSING_FIELDS

        # Test non-sequential indices
        with pytest.raises(MTWSElementError) as exc_info:
            CommonMessageElementList(
                elements=[
                    CommonMessageElement(
                        index=0,
                        fields=[CommonMessageField(name="field1", value="test")],
                    ),
                    CommonMessageElement(
                        index=2,  # Missing index 1
                        fields=[CommonMessageField(name="field2", value="test")],
                    ),
                ]
            )
        assert exc_info.value.error_code == MTWSElementError.NON_SEQUENTIAL

        # Test invalid elements data type
        with pytest.raises(MTWSElementError) as exc_info:
            CommonMessageElementList.from_dict("invalid")  # type: ignore
        assert exc_info.value.error_code == MTWSElementError.INVALID_STRUCTURE

    def test_field_value_edge_cases(self):
        """Test field value conversion edge cases."""
        # Test empty string value
        field = CommonMessageField(name="test", value="")
        assert field.value == ""

        # Test value setter with non-string
        field = CommonMessageField(name="test", value=123)
        field.value = [1, 2, 3]  # Should convert to string
        assert field.value == "[1, 2, 3]"

        # Test value setter with empty string
        field = CommonMessageField(name="test", value="test")
        field.value = ""
        assert field.value == ""

        # Test value setter with special characters
        field = CommonMessageField(name="test", value="test")
        field.value = "!@#$%^&*()"
        assert field.value == "!@#$%^&*()"

    def test_field_validation_edge_cases(self):
        """Test field validation edge cases."""
        # Test field with both value and message
        with pytest.raises(MTWSFieldError) as exc_info:
            CommonMessageField(
                name="test",
                value="test",
                message=CommonMessage(
                    name="nested",
                    sin=16,
                    min_value=1,
                    version=PROTOCOL_VERSION,
                    is_forward=False,
                ),
            )
        assert exc_info.value.error_code == MTWSFieldError.MULTIPLE_VALUES

        # Test field with both value and elements
        with pytest.raises(MTWSFieldError) as exc_info:
            CommonMessageField(
                name="test",
                value="test",
                elements=CommonMessageElementList(
                    elements=[
                        CommonMessageElement(
                            index=0,
                            fields=[CommonMessageField(name="field1", value="test")],
                        )
                    ]
                ),
            )
        assert exc_info.value.error_code == MTWSFieldError.MULTIPLE_VALUES

        # Test field with invalid name type
        with pytest.raises(MTWSFieldError) as exc_info:
            CommonMessageField(name=123, value="test")  # type: ignore
        assert exc_info.value.error_code == MTWSFieldError.INVALID_TYPE

        # Test field with name too long
        with pytest.raises(MTWSFieldError) as exc_info:
            CommonMessageField(name="a" * (MAX_NAME_LENGTH + 1), value="test")
        assert exc_info.value.error_code == MTWSFieldError.INVALID_LENGTH

    def test_message_validation_edge_cases(self):
        """Test message validation edge cases."""
        # Test invalid SIN type
        with pytest.raises(MTWSFieldError) as exc_info:
            CommonMessage(
                name="test",
                sin="16",  # type: ignore
                min_value=1,
                version=PROTOCOL_VERSION,
                is_forward=False,
            )
        assert exc_info.value.error_code == MTWSFieldError.INVALID_TYPE

        # Test invalid MIN type
        with pytest.raises(MTWSFieldError) as exc_info:
            CommonMessage(
                name="test",
                sin=16,
                min_value="1",  # type: ignore
                version=PROTOCOL_VERSION,
                is_forward=False,
            )
        assert exc_info.value.error_code == MTWSFieldError.INVALID_TYPE

        # Test invalid version type
        with pytest.raises(MTWSFieldError) as exc_info:
            CommonMessage(
                name="test",
                sin=16,
                min_value=1,
                version=1.0,  # type: ignore
                is_forward=False,
            )
        assert exc_info.value.error_code == MTWSFieldError.INVALID_TYPE

        # Test missing name in from_dict
        with pytest.raises(MTWSFieldError) as exc_info:
            CommonMessage.from_dict(
                {
                    "SIN": 16,
                    "MIN": 1,
                    "Version": PROTOCOL_VERSION,
                    "IsForward": False,
                }
            )
        assert exc_info.value.error_code == MTWSFieldError.MISSING_VALUE

    def test_create_message(self):
        """Test creating a message."""
        message = CommonMessage(
            name="test",
            sin=1,
            min_value=1,
            version=PROTOCOL_VERSION,
            is_forward=True,
            sequence=1,
            fields=[
                CommonMessageField(
                    name="field1", field_type=FieldValueType.STRING.value, value="test"
                )
            ],
        )
        assert message.name == "test"
        assert message.sin == 1
        assert message.min_value == 1
        assert message.version == PROTOCOL_VERSION
        assert message.is_forward is True
        assert message.sequence == 1
        assert len(message.fields) == 1

    def test_field_validation(self):
        """Test field validation."""
        field = CommonMessageField(
            name="test", field_type=FieldValueType.STRING.value, value="test"
        )
        assert field.name == "test"
        assert field.type == FieldValueType.STRING.value
        assert field.value == "test"
