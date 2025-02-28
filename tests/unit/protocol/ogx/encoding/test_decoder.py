"""Unit tests for OGx JSON decoding functionality.

This module implements tests for OGx message decoding as defined in OGWS-1.txt specifications.
All tests follow the protocol requirements for message format and validation.

Implementation Notes:
- Follows OGWS-1.txt Section 5.1 for message format
- Validates against protocol specifications
- Maintains test relationships with base implementations
"""

import json
from datetime import datetime, timezone

import pytest

from Protexis_Command.api.config import MessageState
from Protexis_Command.api.encoding.json.decoder import (
    OGxJsonDecoder,
    decode_message,
    decode_metadata,
    decode_state,
)
from Protexis_Command.protocols.ogx.models.ogx_messages import OGxMessage
from Protexis_Command.protocols.ogx.validation.ogx_validation_exceptions import EncodingError


@pytest.fixture
def valid_state_json() -> str:
    """Fixture providing valid state JSON for testing."""
    return json.dumps(
        {
            "State": MessageState.ACCEPTED.value,
            "Timestamp": "2024-01-01T00:00:00Z",
            "Metadata": {"Key": "Value"},
        }
    )


@pytest.fixture
def valid_metadata_json() -> str:
    """Fixture providing valid metadata JSON for testing."""
    return json.dumps(
        {"Key1": "string_value", "Key2": 123, "Key3": True, "Key4": None, "Key5": 3.14}
    )


@pytest.fixture
def valid_message_json() -> str:
    """Fixture providing valid message JSON for testing.

    Follows OGWS-1.txt Section 5.1 message format requirements:
    - Required fields: Name, SIN, MIN
    - Fields must be array of field objects
    - Each field must have Name and Value with proper casing
    """
    return json.dumps(
        {
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
    )


@pytest.mark.dependency(depends=["test_ogx_base_decoder"])
class TestOGxJsonDecoder:
    """Test suite for OGxJsonDecoder class.

    Extends base decoder tests with OGWS-specific requirements.
    """

    def test_decode_basic_types(self):
        """Test decoding of basic data types."""
        decoder = OGxJsonDecoder()
        data = {"String": "test", "Integer": 123, "Float": 3.14, "Boolean": True, "Null": None}
        encoded = json.dumps(data)
        decoded = decoder.decode(encoded)
        assert decoded == data

    def test_decode_datetime(self):
        """Test decoding of datetime objects per OGWS format."""
        decoder = OGxJsonDecoder()
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f%z")
        data = {"Timestamp": now}
        encoded = json.dumps(data)
        decoded = decoder.decode(encoded)
        assert isinstance(decoded["Timestamp"], str)
        # Verify OGWS datetime format
        datetime.strptime(decoded["Timestamp"], "%Y-%m-%d %H:%M:%S.%f%z")

    def test_decode_non_dict_data(self):
        """Test handling of non-dictionary JSON data."""
        decoder = OGxJsonDecoder()
        with pytest.raises(EncodingError, match="Decoded data must be a JSON object"):
            decoder.decode(json.dumps([1, 2, 3]))


@pytest.mark.dependency(depends=["test_ogx_base_decoder"])
class TestDecodeState:
    """Test suite for decode_state function.

    Validates state decoding per OGWS-1.txt specifications.
    """

    def test_valid_state(self, valid_state_json):
        """Test decoding of valid state JSON."""
        decoded = decode_state(valid_state_json)
        assert isinstance(decoded["State"], MessageState)
        assert decoded["State"] == MessageState.ACCEPTED
        assert decoded["Timestamp"] == "2024-01-01T00:00:00Z"
        assert decoded["Metadata"] == {"Key": "Value"}

    def test_missing_required_fields(self):
        """Test handling of missing required fields per OGWS spec."""
        with pytest.raises(EncodingError, match="Missing required field: State"):
            decode_state(json.dumps({"Timestamp": "2024-01-01T00:00:00Z"}))

        with pytest.raises(EncodingError, match="Missing required field: Timestamp"):
            decode_state(json.dumps({"State": MessageState.ACCEPTED.value}))

    def test_invalid_state_value(self):
        """Test handling of invalid state values."""
        invalid_json = json.dumps({"State": "invalid", "Timestamp": "2024-01-01T00:00:00Z"})
        with pytest.raises(EncodingError, match="Invalid state value"):
            decode_state(invalid_json)

    def test_invalid_timestamp_format(self):
        """Test handling of invalid timestamp format."""
        invalid_json = json.dumps(
            {"State": MessageState.ACCEPTED.value, "Timestamp": "invalid-timestamp"}
        )
        with pytest.raises(EncodingError, match="Invalid timestamp format"):
            decode_state(invalid_json)

    def test_invalid_json_input(self):
        """Test handling of invalid JSON input."""
        with pytest.raises(EncodingError, match="Failed to decode"):
            decode_state("not a json string")

    def test_invalid_payload_format(self):
        """Test handling of invalid payload format."""
        invalid_json = json.dumps(
            {
                "State": MessageState.ACCEPTED.value,
                "Timestamp": "2024-01-01T00:00:00Z",
                "Payload": {"invalid": "format"},
            }
        )
        with pytest.raises(EncodingError, match="Invalid message payload format"):
            decode_state(invalid_json)

    def test_non_dict_state_data(self):
        """Test handling of non-dictionary state data after JSON decode."""
        with pytest.raises(EncodingError, match="State data must be a JSON object"):
            decode_state(json.dumps([1, 2, 3]))  # Array instead of object

    def test_invalid_state_value_complex(self):
        """Test handling of complex invalid state values."""
        invalid_data = {
            "State": "INVALID_STATE",
            "Timestamp": "2024-01-01T00:00:00Z",
        }  # Not a valid MessageState
        with pytest.raises(EncodingError, match="Invalid state value"):
            decode_state(json.dumps(invalid_data))


@pytest.mark.dependency(depends=["test_ogx_base_decoder"])
class TestDecodeMetadata:
    """Test suite for decode_metadata function.

    Validates metadata decoding per OGWS-1.txt specifications.
    """

    def test_valid_metadata(self, valid_metadata_json):
        """Test decoding of valid metadata."""
        decoded = decode_metadata(valid_metadata_json)
        assert isinstance(decoded, dict)
        assert decoded["Key1"] == "string_value"
        assert decoded["Key2"] == 123
        assert decoded["Key3"] is True
        assert decoded["Key4"] is None
        assert decoded["Key5"] == 3.14

    def test_empty_metadata(self):
        """Test handling of empty metadata."""
        assert decode_metadata("{}") == {}
        assert decode_metadata("") == {}

    def test_invalid_json_format(self):
        """Test handling of invalid JSON format."""
        with pytest.raises(EncodingError, match="Failed to decode metadata"):
            decode_metadata("not a json string")

    def test_invalid_metadata_type(self):
        """Test handling of non-object JSON."""
        with pytest.raises(EncodingError, match="Metadata must be a JSON object"):
            decode_metadata(json.dumps([1, 2, 3]))

    def test_invalid_value_type(self):
        """Test handling of invalid value types per OGWS spec."""
        invalid_json = json.dumps({"key": {"nested": "dict"}})
        with pytest.raises(EncodingError, match="Invalid metadata value type"):
            decode_metadata(invalid_json)

    def test_message_metadata_validation(self):
        """Test validation of message-related metadata per OGWS spec."""
        invalid_metadata = {
            "Name": 123,  # Should be string per OGWS-1.txt
            "SIN": "invalid",  # Should be integer per OGWS-1.txt
            "Fields": "not_a_dict",  # Should be array per OGWS-1.txt
        }
        with pytest.raises(EncodingError, match="Invalid message metadata format"):
            decode_metadata(json.dumps(invalid_metadata))

    def test_invalid_metadata_validation(self):
        """Test handling of invalid metadata validation."""
        invalid_json = json.dumps(
            {"Name": "TestMessage", "SIN": "invalid", "Fields": {"not": "array"}}
        )
        with pytest.raises(EncodingError, match="Invalid message metadata format"):
            decode_metadata(invalid_json)

    def test_invalid_metadata_value_type_complex(self):
        """Test handling of complex invalid metadata value types."""
        invalid_data = {"key": {"nested": "dict"}}  # Nested dict not allowed
        with pytest.raises(EncodingError, match="Invalid metadata value type"):
            decode_metadata(json.dumps(invalid_data))


@pytest.mark.dependency(depends=["test_ogx_base_decoder"])
class TestDecodeMessage:
    """Test suite for decode_message function.

    Validates message decoding per OGWS-1.txt Section 5.1 specifications.
    """

    def test_valid_message_json(self, valid_message_json):
        """Test decoding of valid message JSON."""
        decoded = decode_message(valid_message_json)
        assert isinstance(decoded, OGxMessage)
        message_dict = decoded.to_dict()
        assert message_dict["Name"] == "TestMessage"
        assert message_dict["SIN"] == 1
        assert message_dict["MIN"] == 1
        assert len(message_dict["Fields"]) == 2

    def test_valid_message_dict(self, valid_message_json):
        """Test decoding from valid message dictionary."""
        message_dict = json.loads(valid_message_json)
        decoded = decode_message(message_dict)
        assert isinstance(decoded, OGxMessage)
        assert decoded.to_dict() == message_dict

    def test_invalid_message_format(self):
        """Test handling of invalid message format per OGWS spec."""
        invalid_data = {
            "Name": 123,  # Should be string per OGWS-1.txt
            "SIN": "invalid",  # Should be integer per OGWS-1.txt
        }
        with pytest.raises(EncodingError, match="Invalid message format"):
            decode_message(json.dumps(invalid_data))

    def test_invalid_json_input(self):
        """Test handling of invalid JSON input."""
        with pytest.raises(EncodingError, match="Failed to decode"):
            decode_message("not a json string")

    def test_required_fields(self):
        """Test validation of required fields per OGWS-1.txt Section 5.1."""
        missing_fields_data = {
            "Name": "TestMessage",
            # Missing SIN and MIN
            "Fields": [],
        }
        with pytest.raises(EncodingError, match="Invalid message format"):
            decode_message(json.dumps(missing_fields_data))

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
            decode_message(json.dumps(invalid_fields_data))

    def test_message_creation_error(self):
        """Test handling of message creation errors."""
        # Mock OGxMessage.from_dict to raise an error
        original_from_dict = OGxMessage.from_dict
        try:
            OGxMessage.from_dict = staticmethod(
                lambda data: (_ for _ in ()).throw(ValueError("Mock error"))
            )  # type: ignore

            invalid_data = {
                "Name": "TestMessage",
                "SIN": 1,
                "MIN": 1,
                "Fields": [{"Name": "field1", "Value": "value1"}],
            }
            with pytest.raises(EncodingError, match="Failed to create message object"):
                decode_message(invalid_data)
        finally:
            OGxMessage.from_dict = original_from_dict

    def test_invalid_message_format_complex(self):
        """Test handling of complex invalid message formats."""
        invalid_data = {
            "Name": "TestMessage",
            "SIN": "not_an_integer",
            "MIN": 1,
            "Fields": [],
        }  # Should be integer
        with pytest.raises(EncodingError, match="Invalid message format"):
            decode_message(json.dumps(invalid_data))
