"""Additional tests for MTWS protocol message models.

This module contains additional tests to improve coverage of the message models
implementation defined in N206 section 2.4.1.
"""

import pytest

from protocols.mtws.constants import PROTOCOL_VERSION
from protocols.mtws.exceptions import MTWSElementError, MTWSFieldError
from protocols.mtws.models.messages import (
    CommonMessage,
    CommonMessageElement,
    CommonMessageElementList,
    CommonMessageField,
    FieldValueType,
)


def test_field_value_type_enum():
    """Test FieldValueType enum values."""
    assert FieldValueType.STRING.value == "string"
    assert FieldValueType.INTEGER.value == "integer"
    assert FieldValueType.FLOAT.value == "float"
    assert FieldValueType.BOOLEAN.value == "boolean"
    assert FieldValueType.DATETIME.value == "datetime"
    assert FieldValueType.BINARY.value == "binary"


def test_common_message_element_validation():
    """Test validation of CommonMessageElement."""
    # Test invalid index type
    with pytest.raises(MTWSElementError) as exc_info:
        CommonMessageElement(
            index="not_an_int",  # type: ignore
            fields=[CommonMessageField(name="test", value="test")],
        )
    assert exc_info.value.error_code == MTWSElementError.INVALID_INDEX

    # Test negative index
    with pytest.raises(MTWSElementError) as exc_info:
        CommonMessageElement(
            index=-1,
            fields=[CommonMessageField(name="test", value="test")],
        )
    assert exc_info.value.error_code == MTWSElementError.NEGATIVE_INDEX

    # Test missing fields
    with pytest.raises(MTWSElementError) as exc_info:
        CommonMessageElement(index=0, fields=[])
    assert exc_info.value.error_code == MTWSElementError.MISSING_FIELDS

    # Test duplicate field names
    with pytest.raises(MTWSElementError) as exc_info:
        CommonMessageElement(
            index=0,
            fields=[
                CommonMessageField(name="test", value="value1"),
                CommonMessageField(name="test", value="value2"),
            ],
        )
    assert exc_info.value.error_code == MTWSElementError.INVALID_FIELDS


def test_common_message_element_list_validation():
    """Test validation of CommonMessageElementList."""
    # Test empty elements list
    with pytest.raises(MTWSElementError) as exc_info:
        CommonMessageElementList(elements=[])
    assert exc_info.value.error_code == MTWSElementError.MISSING_FIELDS

    # Test non-sequential indices
    elements = [
        CommonMessageElement(index=0, fields=[CommonMessageField(name="test1", value="value1")]),
        CommonMessageElement(
            index=2, fields=[CommonMessageField(name="test2", value="value2")]  # Missing index 1
        ),
    ]
    with pytest.raises(MTWSElementError) as exc_info:
        CommonMessageElementList(elements=elements)
    assert exc_info.value.error_code == MTWSElementError.NON_SEQUENTIAL


def test_common_message_field_validation():
    """Test validation of CommonMessageField."""
    # Test empty name
    with pytest.raises(MTWSFieldError) as exc_info:
        CommonMessageField(name="", value="test")
    assert exc_info.value.error_code == MTWSFieldError.INVALID_NAME

    # Test invalid name type
    with pytest.raises(MTWSFieldError) as exc_info:
        CommonMessageField(name=123, value="test")  # type: ignore
    assert exc_info.value.error_code == MTWSFieldError.INVALID_TYPE

    # Test multiple values
    with pytest.raises(MTWSFieldError) as exc_info:
        CommonMessageField(
            name="test",
            value="value",
            message=CommonMessage(name="msg", sin=1, min_value=1),
        )
    assert exc_info.value.error_code == MTWSFieldError.MULTIPLE_VALUES

    # Test no value
    with pytest.raises(MTWSFieldError) as exc_info:
        CommonMessageField(name="test")
    assert exc_info.value.error_code == MTWSFieldError.MISSING_VALUE


def test_common_message_validation():
    """Test validation of CommonMessage."""
    # Test invalid name type
    with pytest.raises(MTWSFieldError) as exc_info:
        CommonMessage(name=123, sin=1, min_value=1)  # type: ignore
    assert exc_info.value.error_code == MTWSFieldError.INVALID_TYPE

    # Test invalid SIN
    with pytest.raises(MTWSFieldError) as exc_info:
        CommonMessage(name="test", sin=-1, min_value=1)
    assert exc_info.value.error_code == MTWSFieldError.INVALID_VALUE

    # Test invalid MIN
    with pytest.raises(MTWSFieldError) as exc_info:
        CommonMessage(name="test", sin=1, min_value=-1)
    assert exc_info.value.error_code == MTWSFieldError.INVALID_VALUE

    # Test invalid sequence
    with pytest.raises(MTWSFieldError) as exc_info:
        CommonMessage(name="test", sin=1, min_value=1, sequence=-1)
    assert exc_info.value.error_code == MTWSFieldError.INVALID_VALUE


def test_message_json_serialization():
    """Test JSON serialization of message objects."""
    # Create a complex message structure
    message = CommonMessage(
        name="test",
        sin=1,
        min_value=1,
        version=PROTOCOL_VERSION,
        is_forward=True,
        sequence=1,
        fields=[
            CommonMessageField(
                name="field1", value="value1", field_type=FieldValueType.STRING.value
            ),
            CommonMessageField(
                name="field2",
                elements=CommonMessageElementList(
                    elements=[
                        CommonMessageElement(
                            index=0,
                            fields=[
                                CommonMessageField(name="sub1", value="subval1"),
                                CommonMessageField(name="sub2", value="subval2"),
                            ],
                        )
                    ]
                ),
            ),
        ],
    )

    # Test __json__ method
    json_dict = message.__json__()
    assert isinstance(json_dict, dict)
    assert json_dict["Name"] == "test"
    assert json_dict["SIN"] == 1
    assert json_dict["MIN"] == 1
    assert json_dict["Version"] == PROTOCOL_VERSION
    assert json_dict["IsForward"] is True
    assert json_dict["Sequence"] == 1
    assert len(json_dict["Fields"]) == 2

    # Test field __json__ method
    field_json = message.fields[0].__json__()
    assert isinstance(field_json, dict)
    assert field_json["Name"] == "field1"
    assert field_json["Value"] == "value1"
    assert field_json["Type"] == FieldValueType.STRING.value

    # Test element __json__ method
    if message.fields[1].elements:  # Added null check
        element_json = message.fields[1].elements.elements[0].__json__()
        assert isinstance(element_json, dict)
        assert element_json["Index"] == 0
        assert len(element_json["Fields"]) == 2
