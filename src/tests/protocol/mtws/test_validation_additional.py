"""Additional tests for MTWS protocol validation.

This module contains additional tests to improve coverage of the validation
implementation defined in N206 section 2.4.3.
"""

import pytest

from protocols.mtws.constants import (
    FIELD_VALUE_BASE_SIZE,
    MAX_MESSAGE_SIZE,
    MAX_VALUE_LENGTH,
    PROTOCOL_VERSION,
)
from protocols.mtws.exceptions import MTWSElementError, MTWSFieldError, MTWSSizeError
from protocols.mtws.validation.validation import MTWSMessageSizeComponents, MTWSProtocolValidator


def test_message_size_components():
    """Test message size components initialization."""
    components = MTWSMessageSizeComponents()
    assert components.message_envelope > 0
    assert components.message_name_base > 0
    assert components.sin_base > 0
    assert components.min_base > 0
    assert components.fields_envelope > 0
    assert components.field_envelope > 0
    assert components.field_name_base > 0
    assert components.elements_envelope > 0
    assert components.index_base > 0


def test_calculate_field_size_invalid_input():
    """Test field size calculation with invalid input."""
    validator = MTWSProtocolValidator()

    # Test non-dict input
    with pytest.raises(MTWSFieldError) as exc_info:
        validator.calculate_field_size([])  # type: ignore
    assert exc_info.value.error_code == MTWSFieldError.INVALID_TYPE

    # Test missing name
    with pytest.raises(MTWSFieldError) as exc_info:
        validator.calculate_field_size({"Value": "test"})
    assert exc_info.value.error_code == MTWSFieldError.INVALID_NAME

    # Test value exceeding size limit
    with pytest.raises(MTWSSizeError) as exc_info:
        validator.calculate_field_size({"Name": "test", "Value": "x" * (MAX_VALUE_LENGTH + 1)})
    assert exc_info.value.error_code == MTWSSizeError.EXCEEDS_FIELD_SIZE


def test_calculate_elements_size_invalid_input():
    """Test elements size calculation with invalid input."""
    validator = MTWSProtocolValidator()

    # Test non-list input
    with pytest.raises(MTWSElementError) as exc_info:
        validator.calculate_elements_size({})  # type: ignore
    assert exc_info.value.error_code == MTWSElementError.INVALID_STRUCTURE

    # Test empty list
    with pytest.raises(MTWSElementError) as exc_info:
        validator.calculate_elements_size([])
    assert exc_info.value.error_code == MTWSElementError.MISSING_FIELDS


def test_calculate_message_size_edge_cases():
    """Test message size calculation edge cases."""
    validator = MTWSProtocolValidator()

    # Test message with no fields
    size = validator.calculate_message_size(
        {"Name": "test", "SIN": 1, "MIN": 1, "Version": PROTOCOL_VERSION}
    )
    assert size > 0

    # Test message with empty fields array
    size = validator.calculate_message_size(
        {"Name": "test", "SIN": 1, "MIN": 1, "Version": PROTOCOL_VERSION, "Fields": []}
    )
    assert size > 0


def test_validate_message_size_edge_cases():
    """Test message size validation edge cases."""
    validator = MTWSProtocolValidator()

    # Test empty message
    validator.validate_message_size("{}")

    # Test message at size limit
    max_json = "{" + "x" * (MAX_MESSAGE_SIZE - 2) + "}"
    with pytest.raises(MTWSSizeError) as exc_info:
        validator.validate_message_size(max_json)
    assert exc_info.value.error_code == MTWSSizeError.EXCEEDS_MESSAGE_SIZE


def test_validate_field_constraints_edge_cases():
    """Test field constraints validation edge cases."""
    validator = MTWSProtocolValidator()

    # Test non-dict input
    with pytest.raises(MTWSFieldError) as exc_info:
        validator.validate_field_constraints([])  # type: ignore
    assert exc_info.value.error_code == MTWSFieldError.INVALID_TYPE

    # Test empty name
    with pytest.raises(MTWSFieldError) as exc_info:
        validator.validate_field_constraints({"Name": ""})
    assert exc_info.value.error_code == MTWSFieldError.INVALID_NAME

    # Test value at size limit
    field = {"Name": "test", "Value": "x" * (MAX_VALUE_LENGTH - FIELD_VALUE_BASE_SIZE)}
    validator.validate_field_constraints(field)

    # Test value exceeding size limit
    field = {"Name": "test", "Value": "x" * (MAX_VALUE_LENGTH + 1)}
    with pytest.raises(MTWSSizeError) as exc_info:
        validator.validate_field_constraints(field)
    assert exc_info.value.error_code == MTWSSizeError.EXCEEDS_FIELD_SIZE


def test_validate_elements_constraints():
    """Test elements constraints validation."""
    validator = MTWSProtocolValidator()

    # Test empty elements array
    with pytest.raises(MTWSElementError) as exc_info:
        validator.validate_field_constraints({"Name": "test", "Elements": []})
    assert exc_info.value.error_code == MTWSElementError.MISSING_FIELDS

    # Test missing Index
    with pytest.raises(MTWSElementError) as exc_info:
        validator.validate_field_constraints({"Name": "test", "Elements": [{"Fields": []}]})
    assert exc_info.value.error_code == MTWSElementError.MISSING_FIELDS

    # Test invalid Index type
    with pytest.raises(MTWSElementError) as exc_info:
        validator.validate_field_constraints(
            {"Name": "test", "Elements": [{"Index": "0", "Fields": []}]}
        )
    assert exc_info.value.error_code == MTWSElementError.INVALID_INDEX
