"""Unit tests for OGx JSON encoding functionality.

This module implements tests for OGx message encoding as defined in OGWS-1.txt specifications.
All tests follow the protocol requirements for message format and validation.

Implementation Notes:
- Follows OGWS-1.txt Section 5.1 for message format
- Validates against protocol specifications
- Maintains test relationships with base implementations
"""

import json
from datetime import datetime, timezone
from typing import Any, Dict, cast

import pytest
from typing_extensions import Protocol

from Protexis_Command.api.config import MessageState
from Protexis_Command.api.encoding.json.encoder import (
    OGxJsonEncoder,
    encode_message,
    encode_metadata,
    encode_state,
)
from Protexis_Command.protocols.ogx.models.ogx_messages import OGxMessage
from Protexis_Command.protocols.ogx.validation.ogx_validation_exceptions import EncodingError


class OGxMessageProtocol(Protocol):
    """Protocol for OGxMessage interface."""

    def to_dict(self) -> Dict[str, Any]:
        ...


@pytest.fixture
def valid_state_data() -> Dict[str, Any]:
    """Fixture providing valid state data for testing."""
    return {
        "State": MessageState.ACCEPTED,
        "Timestamp": "2024-01-01T00:00:00Z",
        "Metadata": {"Key": "Value"},
    }


@pytest.fixture
def valid_metadata() -> Dict[str, Any]:
    """Fixture providing valid metadata for testing."""
    return {"Key1": "string_value", "Key2": 123, "Key3": True, "Key4": None, "Key5": 3.14}


@pytest.fixture
def valid_message_data() -> Dict[str, Any]:
    """Fixture providing valid message data for testing.

    Follows OGWS-1.txt Section 5.1 message format requirements:
    - Required fields: Name, SIN, MIN
    - Fields must be array of field objects
    - Each field must have Name and Value with proper casing
    """
    return {
        "Name": "TestMessage",
        "SIN": 1,
        "MIN": 1,
        "Fields": [
            {"Name": "field1", "Value": "value1", "Type": "string"},
            {"Name": "field2", "Value": 123, "Type": "unsignedint"},
        ],
        "Version": "1.0",
        "Timestamp": "2024-01-01T00:00:00Z",
    }


@pytest.mark.dependency(depends=["test_ogx_base_encoder"])
class TestOGxJsonEncoder:
    """Test suite for OGxJsonEncoder class.

    Extends base encoder tests with OGWS-specific requirements.
    """

    def test_encode_basic_types(self):
        """Test encoding of basic data types."""
        encoder = OGxJsonEncoder()
        data = {"String": "test", "Integer": 123, "Float": 3.14, "Boolean": True, "Null": None}
        encoded = encoder.encode(data)
        decoded = json.loads(encoded)
        assert decoded == data

    def test_encode_datetime(self):
        """Test encoding of datetime objects per OGWS format."""
        encoder = OGxJsonEncoder()
        now = datetime.now(timezone.utc)
        data = {"Timestamp": now}
        encoded = encoder.encode(data)
        assert isinstance(encoded, str)
        decoded = json.loads(encoded)
        assert isinstance(decoded["Timestamp"], str)
        # Verify OGWS datetime format
        datetime.strptime(decoded["Timestamp"], "%Y-%m-%d %H:%M:%S.%f%z")


@pytest.mark.dependency(depends=["test_ogx_base_encoder"])
class TestEncodeState:
    """Test suite for encode_state function.

    Validates state encoding per OGWS-1.txt specifications.
    """

    def test_valid_state(self, valid_state_data):
        """Test encoding of valid state data."""
        encoded = encode_state(valid_state_data)
        decoded = json.loads(encoded)
        assert decoded["State"] == MessageState.ACCEPTED.value
        assert decoded["Timestamp"] == "2024-01-01T00:00:00Z"
        assert decoded["Metadata"] == {"Key": "Value"}

    def test_missing_required_fields(self):
        """Test handling of missing required fields per OGWS spec."""
        with pytest.raises(EncodingError, match="Missing required field: State"):
            encode_state(cast(Dict[str, Any], {"Timestamp": "2024-01-01T00:00:00Z"}))

        with pytest.raises(EncodingError, match="Missing required field: Timestamp"):
            encode_state(cast(Dict[str, Any], {"State": MessageState.ACCEPTED}))

    def test_invalid_state_value(self):
        """Test handling of invalid state values."""
        invalid_data = cast(
            Dict[str, Any], {"State": "invalid", "Timestamp": "2024-01-01T00:00:00Z"}
        )
        with pytest.raises(EncodingError, match="Invalid state value"):
            encode_state(invalid_data)

    def test_invalid_timestamp_format(self):
        """Test handling of invalid timestamp format."""
        invalid_data = {"State": MessageState.ACCEPTED, "Timestamp": "invalid-timestamp"}
        with pytest.raises(EncodingError, match="Invalid timestamp format"):
            encode_state(invalid_data)

    def test_non_dict_input(self):
        """Test handling of non-dictionary input."""
        with pytest.raises(EncodingError, match="State data must be a dictionary"):
            encode_state(cast(Dict[str, Any], "not a dict"))


@pytest.mark.dependency(depends=["test_ogx_base_encoder"])
class TestEncodeMetadata:
    """Test suite for encode_metadata function.

    Validates metadata encoding per OGWS-1.txt specifications.
    """

    def test_valid_metadata(self, valid_metadata):
        """Test encoding of valid metadata."""
        encoded = encode_metadata(valid_metadata)
        decoded = json.loads(encoded)
        assert decoded == valid_metadata

    def test_none_metadata(self):
        """Test handling of None metadata."""
        encoded = encode_metadata(None)
        assert encoded == "{}"

    def test_invalid_metadata_type(self):
        """Test handling of invalid metadata type."""
        with pytest.raises(EncodingError, match="Metadata must be a dictionary"):
            encode_metadata(cast(Dict[str, Any], "not a dict"))

    def test_invalid_key_type(self):
        """Test handling of non-string keys."""
        with pytest.raises(EncodingError, match="Metadata key must be string"):
            encode_metadata(cast(Dict[str, Any], {123: "value"}))

    def test_invalid_value_type(self):
        """Test handling of invalid value types per OGWS spec."""
        with pytest.raises(EncodingError, match="Invalid metadata value type"):
            encode_metadata({"key": {"nested": "dict"}})

    def test_message_metadata_validation(self):
        """Test validation of message-related metadata per OGWS spec."""
        invalid_metadata = {
            "Name": 123,  # Should be string per OGWS-1.txt
            "SIN": "invalid",  # Should be integer per OGWS-1.txt
            "Fields": "not_a_dict",  # Should be array per OGWS-1.txt
        }
        with pytest.raises(EncodingError, match="Invalid message metadata format"):
            encode_metadata(invalid_metadata)


@pytest.mark.dependency(depends=["test_ogx_base_encoder"])
class TestEncodeMessage:
    """Test suite for encode_message function.

    Validates message encoding per OGWS-1.txt Section 5.1 specifications.
    """

    def test_valid_message_dict(self, valid_message_data):
        """Test encoding of valid message dictionary."""
        encoded = encode_message(valid_message_data)
        decoded = json.loads(encoded)
        assert decoded == valid_message_data

    def test_valid_message_object(self, valid_message_data):
        """Test encoding of valid OGxMessage object."""

        class MockOGxMessage:
            def __init__(self, data: Dict[str, Any]):
                self._data = data

            def to_dict(self) -> Dict[str, Any]:
                return self._data

        message = MockOGxMessage(valid_message_data)
        encoded = encode_message(cast(OGxMessage, message))
        decoded = json.loads(encoded)
        assert decoded == valid_message_data

    def test_invalid_message_format(self):
        """Test handling of invalid message format per OGWS spec."""
        invalid_data = {
            "Name": 123,  # Should be string per OGWS-1.txt
            "SIN": "invalid",  # Should be integer per OGWS-1.txt
        }
        with pytest.raises(EncodingError, match="Invalid message format"):
            encode_message(invalid_data)

    def test_encoding_error(self):
        """Test handling of JSON encoding errors."""

        class UnserializableObject:
            pass

        invalid_data = {
            "Name": "TestMessage",
            "SIN": 1,
            "MIN": 1,
            "Fields": [{"name": "field1", "value": UnserializableObject()}],
        }
        with pytest.raises(EncodingError, match="Invalid message format"):
            encode_message(invalid_data)

    def test_no_validation(self, valid_message_data):
        """Test encoding without validation."""
        slightly_invalid_data = valid_message_data.copy()
        slightly_invalid_data["extra_field"] = "value"
        encoded = encode_message(slightly_invalid_data, validate=False)
        decoded = json.loads(encoded)
        assert decoded == slightly_invalid_data

    def test_required_fields(self):
        """Test validation of required fields per OGWS-1.txt Section 5.1."""
        missing_fields_data = {
            "Name": "TestMessage",
            # Missing SIN and MIN
            "Fields": [],
        }
        with pytest.raises(EncodingError, match="Invalid message format"):
            encode_message(missing_fields_data)

    def test_field_format(self):
        """Test validation of field format per OGWS-1.txt Section 5.1."""
        invalid_fields_data = {
            "Name": "TestMessage",
            "SIN": 1,
            "MIN": 1,
            "Fields": [
                {"Value": "missing_name"},
                {"Name": "missing_value"},
            ],  # Missing Name  # Missing Value
        }
        with pytest.raises(EncodingError, match="Invalid message format"):
            encode_message(invalid_fields_data)
