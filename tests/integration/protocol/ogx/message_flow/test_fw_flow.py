"""Integration tests for OGx forward message flow functionality.

Tests the complete forward message flow according to OGWS-1.txt specifications.
"""

import pytest
from protocols.ogx.constants import FieldType, MessageType
from protocols.ogx.models.fields import Field, Message
from protocols.ogx.validation.common.types import ValidationContext
from protocols.ogx.services.ogws_protocol_handler import OGWSProtocolHandler
from protocols.ogx.validation.common.validation_exceptions import OGxProtocolError


class MockOGWSHandler(OGWSProtocolHandler):
    """Mock implementation for testing forward message flow."""

    async def authenticate(self, credentials):
        """Mock authentication."""
        self._authenticated = True
        self._bearer_token = "test_token"
        return self._bearer_token

    async def submit_message(self, message, destination_id, transport_type=None):
        """Mock message submission."""
        context = ValidationContext(direction=MessageType.FORWARD, network_type="OGX")
        result = self._validate_message(message, context)
        if not result.is_valid:
            raise OGxProtocolError(f"Validation failed: {', '.join(result.errors)}")
        return "test_message_id", result

    async def get_message_status(self, message_id):
        """Mock status check."""
        return {"State": 1, "StatusUTC": "2024-02-12T00:00:00Z"}

    async def get_messages(self, from_utc, message_type):
        """Mock message retrieval."""
        return []  # Return empty list for testing purposes


@pytest.mark.asyncio
async def test_forward_message_flow():
    """Test basic forward message flow through the gateway."""
    # Create test message using proper field capitalization
    test_message = Message(
        Name="test_message",
        SIN=16,
        MIN=1,
        Fields=[
            Field(Name="string_field", Type=FieldType.STRING, Value="test"),
            Field(Name="int_field", Type=FieldType.SIGNED_INT, Value=42),
        ],
    )

    # Initialize handler
    handler = MockOGWSHandler()
    await handler.authenticate({})  # Mock credentials not needed

    try:
        # Submit message
        message_id, validation_result = await handler.submit_message(
            message=test_message.model_dump(),
            destination_id="OGx-00002000SKY9307",  # Test terminal ID
        )

        # Verify submission
        assert validation_result.is_valid
        assert message_id == "test_message_id"

        # Check message state
        state = await handler.get_message_status(message_id)
        assert state is not None
        assert state["State"] == 1  # RECEIVED state

    except OGxProtocolError as e:
        pytest.fail(f"Message flow failed: {str(e)}")
