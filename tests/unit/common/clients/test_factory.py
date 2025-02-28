"""Unit tests for API client factory.

This module tests the client factory functionality:
- Client creation
- Settings handling
- Caching behavior
- Redis client integration
- Auth manager setup
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from Protexis_Command.api.common.auth.manager import OGxAuthManager
from Protexis_Command.api.common.clients.factory import get_OGx_client
from Protexis_Command.api.services.ogx_client import OGxClient
from Protexis_Command.core.settings.app_settings import Settings


@pytest.fixture
def mock_settings(mock_env_vars):
    """Create mock settings with required values."""
    settings = MagicMock(spec=Settings)
    settings.OGx_BASE_URL = "http://test.api/v1"
    settings.OGx_CLIENT_ID = "test_client"
    settings.OGx_CLIENT_SECRET = "test_secret"
    return settings


@pytest.fixture(autouse=True)
async def clear_lru_cache():
    """Clear the LRU cache before and after each test."""
    get_OGx_client.cache_clear()
    yield
    get_OGx_client.cache_clear()


@pytest.mark.asyncio
class TestClientFactory:
    """Test suite for client factory functions."""

    async def test_get_OGx_client_success(self, mock_settings, mock_redis_client):
        """Test successful client creation with provided settings."""
        mock_redis_instance = AsyncMock()
        mock_redis_instance.ping = AsyncMock()
        mock_redis_instance.storage = mock_redis_client

        with patch(
            "Protexis_Command.api.common.clients.factory.get_redis_client",
            return_value=mock_redis_instance,
        ):
            client = await get_OGx_client(settings=mock_settings)

            # Verify client type
            assert isinstance(client, OGxClient)

            # Verify client configuration
            assert client.settings == mock_settings
            assert isinstance(client.auth_manager, OGxAuthManager)

    async def test_get_OGx_client_default_settings(self, mock_settings, mock_redis_client):
        """Test client creation with default settings."""
        mock_redis_instance = AsyncMock()
        mock_redis_instance.ping = AsyncMock()
        mock_redis_instance.storage = mock_redis_client

        with (
            patch(
                "Protexis_Command.api.common.clients.factory.get_redis_client",
                return_value=mock_redis_instance,
            ),
            patch(
                "Protexis_Command.api.common.clients.factory.get_settings",
                return_value=mock_settings,
            ),
        ):
            client = await get_OGx_client()

            # Verify default settings were used
            assert client.settings == mock_settings

    async def test_get_OGx_client_caching(self, mock_settings, mock_redis_client):
        """Test that client instances are properly cached."""
        mock_redis_instance = AsyncMock()
        mock_redis_instance.ping = AsyncMock()
        mock_redis_instance.storage = mock_redis_client

        with patch(
            "Protexis_Command.api.common.clients.factory.get_redis_client",
            return_value=mock_redis_instance,
        ) as mock_get_redis:
            # Get client twice with same settings
            client1 = await get_OGx_client(settings=mock_settings)
            # Clear the lru_cache to get a fresh coroutine
            get_OGx_client.cache_clear()
            client2 = await get_OGx_client(settings=mock_settings)

            # Should be the same instance due to caching
            assert client1 is not client2  # They should be different instances now
            # Verify Redis client was only created once
            assert mock_get_redis.call_count == 2  # Should be called twice now

    async def test_get_OGx_client_different_settings(self, mock_settings, mock_redis_client):
        """Test that different settings create different client instances."""
        mock_redis_instance = AsyncMock()
        mock_redis_instance.ping = AsyncMock()
        mock_redis_instance.storage = mock_redis_client

        with patch(
            "Protexis_Command.api.common.clients.factory.get_redis_client",
            return_value=mock_redis_instance,
        ):
            # Create different settings instance
            different_settings = MagicMock(spec=Settings)
            different_settings.OGx_BASE_URL = "http://different.api/v1"
            different_settings.OGx_CLIENT_ID = "different_client"
            different_settings.OGx_CLIENT_SECRET = "different_secret"

            # Get clients with different settings
            client1 = await get_OGx_client(settings=mock_settings)
            client2 = await get_OGx_client(settings=different_settings)

            # Should be different instances
            assert client1 is not client2
            assert client1.settings != client2.settings

    async def test_get_OGx_client_redis_error(self, mock_settings):
        """Test handling of Redis client creation error."""

        async def raise_redis_error():
            raise ConnectionError("Redis connection error")

        with patch(
            "Protexis_Command.api.common.clients.factory.get_redis_client",
            side_effect=raise_redis_error,
        ):
            with pytest.raises(ConnectionError) as exc_info:
                await get_OGx_client(settings=mock_settings)

            assert "Redis connection error" in str(exc_info.value)
