"""End-to-end tests for OGx forward message flow.

These tests verify the complete forward message flow using real OGx API
and services. They require:
1. Valid OGx credentials
2. Running Redis instance
3. Network access to OGx
4. Proper environment setup
"""

import asyncio
from datetime import datetime

import pytest
from core.app_settings import get_settings
from protocols.ogx.constants import FieldType, TransportType
from protocols.ogx.models.fields import Field, Message
from protocols.ogx.services.OGx_protocol_handler import OGxProtocolHandler
from protocols.ogx.validation.common.validation_exceptions import OGxProtocolError


@pytest.mark.e2e
@pytest.mark.external_api
@pytest.mark.requires_credentials
@pytest.mark.slow
async def test_forward_message_flow_e2e():
    """Test complete forward message flow with real OGx API.

    This test:
    1. Creates a real message
    2. Submits to actual OGx API
    3. Verifies submission
    4. Tracks message state
    5. Cleans up after test
    """
    settings = get_settings()

    # Skip if no credentials
    if not all([settings.OGx_CLIENT_ID, settings.OGx_CLIENT_SECRET]):
        pytest.skip("OGx credentials not configured")

    # Create test message
    test_message = Message(
        Name=f"e2e_test_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
        SIN=16,
        MIN=1,
        Fields=[
            Field(Name="string_field", Type=FieldType.STRING, Value="e2e_test"),
            Field(Name="int_field", Type=FieldType.SIGNED_INT, Value=42),
        ],
    )

    # Get real protocol handler
    handler = OGxProtocolHandler()  # This will be replaced with real implementation

    try:
        # Authenticate
        await handler.authenticate(
            {"client_id": settings.OGx_CLIENT_ID, "client_secret": settings.OGx_CLIENT_SECRET}
        )

        # Submit message
        message_id, validation_result = await handler.submit_message(
            message=test_message.model_dump(),
            destination_id=settings.OGx_TEST_MOBILE_ID,
            transport_type=TransportType.SATELLITE,
        )

        # Verify submission
        assert validation_result.is_valid
        assert message_id is not None

        # Track message state (with timeout)
        max_wait = 300  # 5 minutes
        start_time = datetime.utcnow()
        final_state = None

        while (datetime.utcnow() - start_time).total_seconds() < max_wait:
            state = await handler.get_message_status(message_id)
            if state["State"] in [2, 3, 4]:  # ERROR, DELIVERY_FAILED, TIMED_OUT
                pytest.fail(f"Message failed with state: {state['State']}")
            if state["State"] == 1:  # RECEIVED
                final_state = state
                break
            await asyncio.sleep(10)  # Check every 10 seconds

        assert final_state is not None, "Message did not reach RECEIVED state"
        assert final_state["State"] == 1

    except OGxProtocolError as e:
        pytest.fail(f"E2E test failed: {str(e)}")

    finally:
        # Cleanup if needed
        pass  # Add cleanup code if required
