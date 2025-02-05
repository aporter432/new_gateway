"""Tests for MTWS protocol validator implementation.

This module contains tests that verify the protocol validation functionality
follows the specifications defined in N206 section 2.4.3.
"""

import json

import pytest

from protocols.mtws.constants import (
    FIELD_VALUE_BASE_SIZE,
    MAX_MESSAGE_SIZE,
    MAX_NAME_LENGTH,
    MAX_VALUE_LENGTH,
    PROTOCOL_VERSION,
)
from protocols.mtws.exceptions import (
    MTWSElementError,
    MTWSFieldError,
    MTWSSizeError,
)
from protocols.mtws.models.messages import (
    CommonMessage,
    CommonMessageElement,
    CommonMessageElementList,
    CommonMessageField,
)
from protocols.mtws.validation.validation import MTWSProtocolValidator


@pytest.fixture(name="validator")
def validator_fixture():
    """Create a protocol validator instance for testing."""
    return MTWSProtocolValidator()


class TestMTWSProtocolValidator:
    """Test suite for MTWS protocol validator implementation."""

    def test_validate_message_structure(self, validator):
        """Test validation of basic message structure requirements."""
        # Valid message structure
        valid_message = CommonMessage(
            name="test",
            sin=16,
            min_value=1,
            is_forward=False,
            version=PROTOCOL_VERSION,
            fields=[CommonMessageField(name="field1", value="test")],
        )
        validator.validate_message(valid_message.to_dict())  # Should not raise

        # Missing required fields
        with pytest.raises(MTWSFieldError) as exc_info:
            validator.validate_message({"Name": "test"})
        assert exc_info.value.error_code == MTWSFieldError.MISSING_VALUE

    def test_field_size_constraints(self, validator):
        """Test field size constraint validation according to N206 section 2.4.3.1."""
        # Valid field size
        valid_field = CommonMessageField(name="test", value="value")
        validator.validate_field_constraints(valid_field.to_dict())  # Should not raise

        # Field name too long (>32 chars)
        with pytest.raises(MTWSFieldError) as exc_info:
            validator.validate_field_constraints(
                {
                    "Name": "a" * (MAX_NAME_LENGTH + 1),
                    "Value": "test",
                }
            )
        assert exc_info.value.error_code == MTWSFieldError.INVALID_LENGTH

        # Field value too large (>1KB)
        with pytest.raises(MTWSSizeError) as exc_info:
            validator.validate_field_constraints(
                {
                    "Name": "test",
                    "Value": "x" * (MAX_VALUE_LENGTH - FIELD_VALUE_BASE_SIZE + 1),
                }
            )
        assert exc_info.value.error_code == MTWSSizeError.EXCEEDS_FIELD_SIZE

    def test_element_validation(self, validator):
        """Test validation of array elements."""
        # Valid array structure
        valid_array = CommonMessage(
            name="test",
            sin=16,
            min_value=1,
            is_forward=False,
            version=PROTOCOL_VERSION,
            fields=[
                CommonMessageField(
                    name="array",
                    elements=CommonMessageElementList(
                        elements=[
                            CommonMessageElement(
                                index=0, fields=[CommonMessageField(name="field1", value="test")]
                            )
                        ]
                    ),
                )
            ],
        )
        validator.validate_message(valid_array.to_dict())  # Should not raise

        # Invalid element index (negative)
        with pytest.raises(MTWSElementError) as exc_info:
            validator.validate_message(
                {
                    "Name": "test",
                    "SIN": 16,
                    "MIN": 1,
                    "Version": PROTOCOL_VERSION,
                    "IsForward": False,
                    "Fields": [
                        {
                            "Name": "array",
                            "Elements": [
                                {
                                    "Index": -1,  # Must be non-negative
                                    "Fields": [{"Name": "field1", "Value": "test"}],
                                }
                            ],
                        }
                    ],
                }
            )
        assert exc_info.value.error_code == MTWSElementError.NEGATIVE_INDEX

    def test_nested_structure_validation(self, validator):
        """Test validation of nested message structures."""
        # Valid nested structure
        valid_nested = CommonMessage(
            name="test",
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
                                                            name="value", value="test"
                                                        )
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
        validator.validate_message(valid_nested.to_dict())  # Should not raise

    def test_field_name_uniqueness(self, validator):
        """Test validation of field name uniqueness."""
        # Valid field names (unique)
        valid_fields = CommonMessage(
            name="test",
            sin=16,
            min_value=1,
            is_forward=False,
            version=PROTOCOL_VERSION,
            fields=[
                CommonMessageField(name="field1", value="test1"),
                CommonMessageField(name="field2", value="test2"),
            ],
        )
        validator.validate_message(valid_fields.to_dict())  # Should not raise

        # Duplicate field names
        with pytest.raises(MTWSFieldError) as exc_info:
            validator.validate_message(
                {
                    "Name": "test",
                    "SIN": 16,
                    "MIN": 1,
                    "Version": PROTOCOL_VERSION,
                    "IsForward": False,
                    "Fields": [
                        {"Name": "field", "Value": "test1"},
                        {"Name": "field", "Value": "test2"},  # Duplicate name
                    ],
                }
            )
        assert exc_info.value.error_code == MTWSFieldError.INVALID_NAME

    def test_message_size_calculation(self, validator):
        """Test message size calculation and validation."""
        # Valid message size
        valid_message = CommonMessage(
            name="test",
            sin=16,
            min_value=1,
            is_forward=False,
            version=PROTOCOL_VERSION,
            fields=[CommonMessageField(name="field1", value="test")],
        )
        size = validator.calculate_message_size(valid_message.to_dict())
        assert size > 0  # Size should be positive

        # Test size calculation with nested structure
        nested_message = CommonMessage(
            name="test",
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
                                fields=[CommonMessageField(name="inner", value="test")],
                            )
                        ]
                    ),
                )
            ],
        )
        nested_size = validator.calculate_message_size(nested_message.to_dict())
        assert nested_size > size  # Nested structure should be larger

    def test_field_size_calculation(self, validator):
        """Test field size calculation."""
        # Test field with value
        field_size = validator.calculate_field_size({"Name": "test", "Value": "test"})
        assert field_size > 0

        # Test field with elements
        field_size = validator.calculate_field_size(
            {
                "Name": "test",
                "Elements": [{"Index": 0, "Fields": [{"Name": "inner", "Value": "test"}]}],
            }
        )
        assert field_size > 0

        # Test field with nested message
        field_size = validator.calculate_field_size(
            {
                "Name": "test",
                "Message": {
                    "Name": "nested",
                    "SIN": 16,
                    "MIN": 1,
                    "Version": PROTOCOL_VERSION,
                    "IsForward": False,
                    "Fields": [{"Name": "inner", "Value": "test"}],
                },
            }
        )
        assert field_size > 0

    def test_message_size_validation(self, validator):
        """Test message size validation according to N206 section 2.4.3."""
        # Test valid message size
        validator.validate_message_size('{"small": "message"}')  # Should not raise

        # Test message exceeding GPRS block size (1KB)
        with pytest.raises(MTWSSizeError) as exc_info:
            large_message = {
                "Name": "test",
                "SIN": 16,
                "MIN": 1,
                "Version": PROTOCOL_VERSION,
                "IsForward": False,
                "Fields": [
                    {
                        "Name": "large_field",
                        "Value": "x" * (MAX_MESSAGE_SIZE - 100),  # Account for message overhead
                    }
                ],
            }
            validator.validate_message_size(json.dumps(large_message))
        assert exc_info.value.error_code == MTWSSizeError.EXCEEDS_MESSAGE_SIZE

        # Test message with HTTP header approaching limit
        with pytest.raises(MTWSSizeError) as exc_info:
            message_with_large_header = {
                "Name": "test" * 50,  # Large name to increase header size
                "SIN": 16,
                "MIN": 1,
                "Version": PROTOCOL_VERSION,
                "IsForward": False,
                "Fields": [{"Name": "field", "Value": "x" * 800}],  # Large value
            }
            validator.validate_message_size(json.dumps(message_with_large_header))
        assert exc_info.value.error_code == MTWSSizeError.EXCEEDS_MESSAGE_SIZE

    def test_size_calculation_edge_cases(self, validator):
        """Test edge cases in size calculation methods."""
        # Test invalid field dictionary
        with pytest.raises(MTWSFieldError) as exc_info:
            validator.calculate_field_size(None)  # type: ignore
        assert exc_info.value.error_code == MTWSFieldError.INVALID_TYPE

        # Test missing field name
        with pytest.raises(MTWSFieldError) as exc_info:
            validator.calculate_field_size({"Value": "test"})
        assert exc_info.value.error_code == MTWSFieldError.INVALID_NAME

        # Test invalid elements structure
        with pytest.raises(MTWSElementError) as exc_info:
            validator.calculate_elements_size(None)  # type: ignore
        assert exc_info.value.error_code == MTWSElementError.INVALID_STRUCTURE

        # Test empty elements list
        with pytest.raises(MTWSElementError) as exc_info:
            validator.calculate_elements_size([])
        assert exc_info.value.error_code == MTWSElementError.MISSING_FIELDS

    def test_validation_error_handling(self, validator):
        """Test error handling in validation methods."""
        # Test invalid message dictionary
        with pytest.raises(MTWSFieldError) as exc_info:
            validator.validate_message(None)  # type: ignore
        assert exc_info.value.error_code == MTWSFieldError.INVALID_TYPE

        # Test invalid field dictionary
        with pytest.raises(MTWSFieldError) as exc_info:
            validator.validate_field_constraints(None)  # type: ignore
        assert exc_info.value.error_code == MTWSFieldError.INVALID_TYPE

        # Test invalid message size input
        with pytest.raises(MTWSSizeError) as exc_info:
            validator.validate_message_size("x" * (MAX_MESSAGE_SIZE + 1))
        assert exc_info.value.error_code == MTWSSizeError.EXCEEDS_MESSAGE_SIZE

        # Test invalid field structure
        with pytest.raises(MTWSFieldError) as exc_info:
            validator.validate_field_constraints({"Name": "test"})  # Missing value/message/elements
        assert exc_info.value.error_code == MTWSFieldError.MISSING_VALUE

    def test_element_validation_edge_cases(self, validator):
        """Test edge cases in element validation."""
        # Test element with missing index
        with pytest.raises(MTWSElementError) as exc_info:
            validator.validate_field_constraints(
                {
                    "Name": "test",
                    "Elements": [{"Fields": [{"Name": "field1", "Value": "test"}]}],
                }
            )
        assert exc_info.value.error_code == MTWSElementError.MISSING_FIELDS

        # Test element with invalid index type
        with pytest.raises(MTWSElementError) as exc_info:
            validator.validate_field_constraints(
                {
                    "Name": "test",
                    "Elements": [
                        {
                            "Index": "0",  # Should be int
                            "Fields": [{"Name": "field1", "Value": "test"}],
                        }
                    ],
                }
            )
        assert exc_info.value.error_code == MTWSElementError.INVALID_INDEX

        # Test element with missing fields
        with pytest.raises(MTWSElementError) as exc_info:
            validator.validate_field_constraints({"Name": "test", "Elements": [{"Index": 0}]})
        assert exc_info.value.error_code == MTWSElementError.MISSING_FIELDS

        # Test element with empty fields array
        with pytest.raises(MTWSElementError) as exc_info:
            validator.validate_field_constraints(
                {"Name": "test", "Elements": [{"Index": 0, "Fields": []}]}
            )
        assert exc_info.value.error_code == MTWSElementError.MISSING_FIELDS


def test_validate_message_size():
    """Test message size validation."""
    validator = MTWSProtocolValidator()
    message = CommonMessage(
        name="test",
        sin=1,
        min_value=1,
        version=PROTOCOL_VERSION,
        is_forward=False,
        fields=[
            CommonMessageField(name="field1", value="test"),
            CommonMessageField(name="field2", value="test"),
        ],
    )

    # Valid message size
    validator.validate_message_size(json.dumps(message.to_dict()))

    # Message too large
    with pytest.raises(MTWSSizeError) as exc_info:
        validator.validate_message_size(
            json.dumps(
                {
                    "Name": "test",
                    "SIN": 1,
                    "MIN": 1,
                    "Version": PROTOCOL_VERSION,
                    "IsForward": False,
                    "Fields": [{"Name": "field1", "Value": "x" * MAX_MESSAGE_SIZE}],
                }
            )
        )
