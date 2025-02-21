"""Tests for OGx message models."""

import pytest

from Protexis_Command.api_ogx.models.ogx_messages import OGxMessage


class TestOGxMessage:
    """Test suite for OGx message functionality."""

    @pytest.fixture
    def valid_message_data(self) -> dict:
        """Fixture providing valid message data."""
        return {
            "Name": "test_message",
            "SIN": 16,
            "MIN": 1,
            "IsForward": True,
            "Fields": [
                {"name": "field1", "value": "test"},
                {"name": "field2", "value": 42},
            ],
        }

    def test_message_initialization(self):
        """Test basic message initialization."""
        fields = [{"name": "field1", "value": "test"}]
        message = OGxMessage(
            name="test_message",
            sin=16,
            min_value=1,
            is_forward=True,
            fields=fields,
        )

        assert message.name == "test_message"
        assert message.sin == 16
        assert message.min == 1
        assert message.is_forward is True
        assert message.fields == fields

    def test_message_initialization_minimal(self):
        """Test message initialization with only required fields."""
        message = OGxMessage(
            name="test_message",
            sin=16,
            min_value=1,
        )

        assert message.name == "test_message"
        assert message.sin == 16
        assert message.min == 1
        assert message.is_forward is None
        assert message.fields == []

    def test_message_from_dict(self, valid_message_data):
        """Test creating message from dictionary."""
        message = OGxMessage.from_dict(valid_message_data)

        assert message.name == valid_message_data["Name"]
        assert message.sin == valid_message_data["SIN"]
        assert message.min == valid_message_data["MIN"]
        assert message.is_forward == valid_message_data["IsForward"]
        assert message.fields == valid_message_data["Fields"]

    def test_message_to_dict(self):
        """Test converting message to dictionary."""
        fields = [{"name": "field1", "value": "test"}]
        message = OGxMessage(
            name="test_message",
            sin=16,
            min_value=1,
            is_forward=True,
            fields=fields,
        )

        expected = {
            "Name": "test_message",
            "SIN": 16,
            "MIN": 1,
            "IsForward": True,
            "Fields": fields,
        }
        assert message.to_dict() == expected

    def test_message_to_dict_minimal(self):
        """Test converting minimal message to dictionary."""
        message = OGxMessage(
            name="test_message",
            sin=16,
            min_value=1,
        )

        expected = {
            "Name": "test_message",
            "SIN": 16,
            "MIN": 1,
        }
        assert message.to_dict() == expected

    def test_message_from_dict_missing_required(self):
        """Test error when required fields are missing."""
        invalid_data = {
            "Name": "test_message",
            # Missing SIN and MIN
        }
        with pytest.raises(ValueError, match="Missing required fields"):
            OGxMessage.from_dict(invalid_data)

    def test_message_from_dict_invalid_input(self):
        """Test error with invalid input type."""
        invalid_input: dict = None  # type: ignore
        with pytest.raises(ValueError, match="Data must be a dictionary"):
            OGxMessage.from_dict(invalid_input)

    def test_message_repr(self):
        """Test string representation of message."""
        message = OGxMessage(
            name="test_message",
            sin=16,
            min_value=1,
        )
        expected = "OGxMessage(name=test_message, sin=16, min=1)"
        assert repr(message) == expected
