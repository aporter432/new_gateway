"""Integration tests for token error handling.

This module tests error handling in token management:
- Network errors
- Invalid tokens
- Expired tokens
- Rate limiting
"""

import time
from typing import AsyncGenerator
from unittest.mock import patch

import pytest
from httpx import HTTPStatusError
from redis.asyncio import Redis

from Protexis_Command.core.app_settings import Settings
from Protexis_Command.protocol.ogx.auth.manager import OGxAuthManager, TokenMetadata
from tests.integration.fixtures.mock_responses import OGxMockResponses
from tests.integration.helpers import RedisHelper

# Use function-scoped event loop for better isolation
pytestmark = [pytest.mark.asyncio, pytest.mark.integration, pytest.mark.requires_redis]


@pytest.fixture
async def redis_helper(redis_client: Redis) -> AsyncGenerator[RedisHelper, None]:
    """Create and clean up RedisHelper for tests."""
    helper = RedisHelper(redis_client)
    yield helper
    # Redis cleanup is handled by conftest.py fixtures


@pytest.fixture
async def invalid_settings(settings: Settings) -> Settings:
    """Create settings with invalid credentials."""
    settings.OGx_CLIENT_ID = "invalid_id"
    settings.OGx_CLIENT_SECRET = "invalid_secret"
    return settings


async def test_invalid_credentials(invalid_settings: Settings, redis_helper: RedisHelper):
    """Test token acquisition with invalid credentials."""
    auth_manager = OGxAuthManager(invalid_settings, redis_helper.client)

    with patch("httpx.AsyncClient.post", return_value=OGxMockResponses.token_invalid_credentials()):
        with pytest.raises(HTTPStatusError) as exc_info:
            await auth_manager.get_valid_token()
        assert isinstance(exc_info.value, HTTPStatusError)
        assert exc_info.value.response.status_code == 401


async def test_expired_token(settings: Settings, redis_helper: RedisHelper):
    """Test handling of expired tokens."""
    auth_manager = OGxAuthManager(settings, redis_helper.client)

    # Store an expired token
    now = time.time()
    expired_metadata = TokenMetadata(
        token="expired_token",
        created_at=now - 7200,  # 2 hours ago
        expires_at=now - 3600,  # 1 hour ago
        last_used=now - 3600,
        validation_count=0,
    )
    await auth_manager._store_token_metadata(expired_metadata)

    # Mock response for new token request
    with patch("httpx.AsyncClient.post", return_value=OGxMockResponses.token_success("new_token")):
        token = await auth_manager.get_valid_token()
        assert token == "new_token"

        # Verify old token was cleaned up
        metadata = await auth_manager._get_token_metadata()
        assert metadata is not None
        assert metadata.token == "new_token"
        assert metadata.expires_at > now


async def test_token_validation_failure(settings: Settings, redis_helper: RedisHelper):
    """Test handling of token validation failures."""
    auth_manager = OGxAuthManager(settings, redis_helper.client)

    # Store a valid token
    now = time.time()
    valid_metadata = TokenMetadata(
        token="test_token",
        created_at=now,
        expires_at=now + 3600,
        last_used=now,
        validation_count=0,
    )
    await auth_manager._store_token_metadata(valid_metadata)

    # Mock validation failure response
    with patch("httpx.AsyncClient.get", return_value=OGxMockResponses.validation_failure()):
        is_valid = await auth_manager.validate_token({"Authorization": "Bearer test_token"})
        assert not is_valid

        # Token should be automatically invalidated after validation failure
        metadata = await auth_manager._get_token_metadata()
        assert metadata is None


async def test_rate_limit_handling(settings: Settings, redis_helper: RedisHelper):
    """Test handling of rate limit responses."""
    auth_manager = OGxAuthManager(settings, redis_helper.client)

    with patch("httpx.AsyncClient.post", return_value=OGxMockResponses.rate_limit_exceeded()):
        with pytest.raises(HTTPStatusError) as exc_info:
            await auth_manager.get_valid_token()
        assert isinstance(exc_info.value, HTTPStatusError)
        assert exc_info.value.response.status_code == 429
        assert "Retry-After" in exc_info.value.response.headers
        assert exc_info.value.response.headers["Retry-After"] == "60"
