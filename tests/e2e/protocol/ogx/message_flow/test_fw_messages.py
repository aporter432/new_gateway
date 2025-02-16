"""End-to-End (E2E) tests for forward message endpoints.

Location: tests/e2e/api/endpoints/test_fw_messages.py

This module tests the forward message API endpoints according to OGWS-1.txt specifications.
These tests require:
1. Valid API credentials
2. Access to external OGWS service
3. Test terminal availability

Important:
    NetworkType Usage:
    - ALWAYS use NetworkType enum from protocols.ogx.constants
    - NEVER use string representations of network types
    - NEVER convert NetworkType to/from strings unless required by external API
    - Example:
        CORRECT:   network_type=NetworkType.OGX
        INCORRECT: network_type="OGX" or network_type="1"

    This ensures type safety and consistency across the codebase.
    The NetworkType enum is the single source of truth for network types.

Test Dependencies:
    - Valid API credentials in environment
    - Running proxy service
    - Network access to OGWS API
    - Test terminal availability
"""

import pytest
from httpx import AsyncClient

from protocols.ogx.constants import FieldType, NetworkType

pytestmark = pytest.mark.asyncio


async def test_forward_message_basic():
    """Test basic forward message submission."""
    async with AsyncClient() as client:
        response = await client.post(
            "http://proxy:8080/api/v1.0/messages/forward",
            json={
                "Name": "test_message",
                "SIN": 16,
                "MIN": 1,
                "Fields": [
                    {"Name": "string_field", "Type": FieldType.STRING.value, "Value": "test"},
                    {"Name": "int_field", "Type": FieldType.SIGNED_INT.value, "Value": 42},
                ],
                "DestinationID": "OGx-00002000SKY9307",  # Test terminal ID
                "Network": NetworkType.OGX.value,  # Use NetworkType enum
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "message_id" in data

        # Check message state
        status_response = await client.get(
            f"http://proxy:8080/api/v1.0/messages/{data['message_id']}/status"
        )
        assert status_response.status_code == 200
        state = status_response.json()
        assert state["State"] == 1  # RECEIVED state
