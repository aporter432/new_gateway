"""Unit tests for MessageSender service."""

import json
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import HTTPStatusError, Response

from core.app_settings import Settings
from protocols.ogx.constants import TransportType
from protocols.ogx.exceptions import OGxProtocolError
from protocols.ogx.services.ogws_message_sender import MessageSender


@pytest.fixture
def settings():
    """Test settings fixture."""
    return Settings(
        OGWS_CLIENT_ID="test_id",
        OGWS_CLIENT_SECRET="test_secret",
        OGWS_BASE_URL="http://test.url",
        CUSTOMER_ID="test_customer",
    )


@pytest.fixture
def mock_logger():
    """Mock logger fixture."""
    return MagicMock(
        info=MagicMock(),
        warning=MagicMock(),
        error=MagicMock(),
    )


@pytest.fixture
def mock_token_metadata():
    """Mock token metadata fixture."""
    now = time.time()
    return {
        "token": "test_token",
        "created_at": now,
        "expires_at": now + 3600,  # 1 hour from now
        "last_used": now,
        "last_validated": now,
        "validation_count": 0,
    }


@pytest.fixture
def mock_auth_response():
    """Mock auth response fixture."""
    mock_response = MagicMock(spec=Response)
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "access_token": "test_token",
        "expires_in": 3600,
        "token_type": "Bearer",
    }
    return mock_response


@pytest.fixture
async def message_sender(settings, mock_logger, mock_token_metadata, mock_auth_response):
    """MessageSender fixture with mocked Redis."""
    with (
        patch("protocols.ogx.services.ogws_message_sender.get_redis_client") as mock_redis,
        patch("protocols.ogx.services.ogws_message_sender.get_settings") as mock_settings,
        patch(
            "protocols.ogx.services.ogws_message_sender.get_protocol_logger"
        ) as mock_protocol_logger,
        patch("core.security.get_auth_logger") as mock_auth_logger,
    ):
        mock_redis_instance = AsyncMock()
        mock_redis_instance.get.return_value = json.dumps(mock_token_metadata)
        mock_redis.return_value = mock_redis_instance
        mock_settings.return_value = settings
        mock_protocol_logger.return_value = mock_logger
        mock_auth_logger.return_value = mock_logger
        sender = MessageSender()
        await sender.initialize()
        return sender


@pytest.mark.asyncio
async def test_send_message_success(message_sender, mock_auth_response):
    """Test successful message sending."""
    test_message = {"DestinationID": "test_dest", "Payload": {"test": "data"}}

    expected_response = {"ErrorID": 0, "MessageID": "12345"}

    async def mock_post_side_effect(url, **kwargs):
        if "/auth/token" in url:
            return mock_auth_response
        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 200
        mock_response.raise_for_status = AsyncMock()
        mock_response.json.return_value = expected_response
        return mock_response

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock, side_effect=mock_post_side_effect):
        response = await message_sender.send_message(test_message)
        assert response == expected_response


@pytest.mark.asyncio
async def test_send_message_with_transport(message_sender, mock_auth_response):
    """Test message sending with specific transport type."""
    test_message = {"DestinationID": "test_dest", "Payload": {"test": "data"}}

    async def mock_post_side_effect(url, **kwargs):
        if "/auth/token" in url:
            return mock_auth_response
        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 200
        mock_response.raise_for_status = AsyncMock()
        mock_response.json.return_value = {"ErrorID": 0}
        return mock_response

    with patch(
        "httpx.AsyncClient.post", new_callable=AsyncMock, side_effect=mock_post_side_effect
    ) as mock_post:
        await message_sender.send_message(test_message, transport=TransportType.SATELLITE)

        # Find the call that sent the message (not the auth call)
        message_call = [
            call for call in mock_post.call_args_list if "/submit/messages" in call[0][0]
        ][0]
        assert message_call[1]["json"]["TransportType"] == TransportType.SATELLITE.value


@pytest.mark.asyncio
async def test_send_message_http_error(message_sender):
    """Test handling of HTTP errors."""
    test_message = {"DestinationID": "test_dest", "Payload": {"test": "data"}}

    with patch("httpx.AsyncClient.post") as mock_post:
        mock_post.side_effect = HTTPStatusError("Error", request=MagicMock(), response=MagicMock())

        with pytest.raises(OGxProtocolError):
            await message_sender.send_message(test_message)


@pytest.mark.asyncio
async def test_submit_batch_success(message_sender):
    """Test successful batch message submission."""
    test_messages = [
        {"DestinationID": "dest1", "Payload": {"test": "data1"}},
        {"DestinationID": "dest2", "Payload": {"test": "data2"}},
    ]

    expected_responses = [
        {"ErrorID": 0, "MessageID": "12345"},
        {"ErrorID": 0, "MessageID": "12346"},
    ]

    with patch.object(message_sender, "send_message") as mock_send:
        mock_send.side_effect = expected_responses

        responses = await message_sender.submit_batch(test_messages)

        assert responses == expected_responses
        assert mock_send.call_count == len(test_messages)


@pytest.mark.asyncio
async def test_handle_rate_limit(message_sender):
    """Test rate limit handling."""
    error_code = 24579  # ERR_SUBMIT_MESSAGE_RATE_EXCEEDED

    with patch("asyncio.sleep") as mock_sleep:
        await message_sender.handle_rate_limit(error_code)
        mock_sleep.assert_called_once()
