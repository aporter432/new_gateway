"""Test suite for error handling in OGWS token management."""

import asyncio
import time
from unittest.mock import patch
import pytest
from httpx import HTTPError

from redis.asyncio import Redis
from redis.exceptions import RedisError

from core.app_settings import Settings
from core.security import OGWSAuthManager, TokenMetadata
from infrastructure.redis import get_redis_client
from tests.api.auth.test_token_setup import get_test_settings, get_test_redis, MockResponse


async def test_invalid_credentials():
    """Test token acquisition with invalid credentials."""
    settings = get_test_settings()
    redis = await get_test_redis()

    try:
        # Mock client to simulate 401 response
        with patch("httpx.AsyncClient") as mock_client:

            async def mock_error_post(*args, **kwargs):
                return MockResponse(401, {"error": "invalid_client"})

            mock_client.return_value.__aenter__.return_value.post = mock_error_post
            mock_client.return_value.__aexit__.return_value = None

            auth_manager = OGWSAuthManager(settings, redis)
            with pytest.raises(HTTPError):
                await auth_manager.get_valid_token()

    finally:
        await redis.aclose()


async def test_network_failure():
    """Test token acquisition with network failure."""
    settings = get_test_settings()
    redis = await get_test_redis()

    try:
        # Mock client to simulate network error
        with patch("httpx.AsyncClient") as mock_client:

            async def mock_network_error(*args, **kwargs):
                raise HTTPError("Connection failed")

            mock_client.return_value.__aenter__.return_value.post = mock_network_error
            mock_client.return_value.__aexit__.return_value = None

            auth_manager = OGWSAuthManager(settings, redis)
            with pytest.raises(HTTPError):
                await auth_manager.get_valid_token()

    finally:
        await redis.aclose()


async def test_redis_failure():
    """Test token operations with Redis failure."""
    settings = get_test_settings()
    redis = await get_test_redis()

    try:
        # Mock Redis to simulate storage error
        with patch.object(Redis, "setex") as mock_setex:
            mock_setex.side_effect = RedisError("Storage failed")

            auth_manager = OGWSAuthManager(settings, redis)
            # Should still get token but log error
            token = await auth_manager.get_valid_token()
            assert token is not None

    finally:
        await redis.aclose()


async def test_expired_token():
    """Test handling of expired tokens."""
    settings = get_test_settings()
    redis = await get_test_redis()

    try:
        auth_manager = OGWSAuthManager(settings, redis)

        # Store an expired token
        now = time.time()
        expired_metadata = TokenMetadata(
            token="expired_token",
            created_at=now - 7200,  # 2 hours ago
            expires_at=now - 3600,  # Expired 1 hour ago
            last_used=now - 3600,
        )
        await auth_manager._store_token_metadata(expired_metadata)

        # Should get new token automatically
        token = await auth_manager.get_valid_token()
        assert token != "expired_token"

        # Verify old token was removed
        metadata_exists = await redis.exists(auth_manager.token_metadata_key)
        assert metadata_exists  # New token metadata should exist

        metadata = await auth_manager._get_token_metadata()
        assert metadata.token != "expired_token"

    finally:
        await redis.delete("ogws:auth:token")
        await redis.delete("ogws:auth:token:metadata")
        await redis.aclose()


async def test_token_validation_failure():
    """Test token validation failure handling."""
    settings = get_test_settings()
    redis = await get_test_redis()

    try:
        # Mock client to simulate validation failure
        with patch("httpx.AsyncClient") as mock_client:

            async def mock_validation_error(*args, **kwargs):
                return MockResponse(401, {"error": "invalid_token"})

            mock_client.return_value.__aenter__.return_value.get = mock_validation_error
            mock_client.return_value.__aexit__.return_value = None

            auth_manager = OGWSAuthManager(settings, redis)
            auth_header = {"Authorization": "Bearer invalid_token"}
            is_valid = await auth_manager.validate_token(auth_header)
            assert not is_valid

    finally:
        await redis.aclose()


if __name__ == "__main__":
    asyncio.run(test_expired_token())
