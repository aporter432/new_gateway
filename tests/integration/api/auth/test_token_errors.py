"""Test suite for error handling in OGWS token management."""

import asyncio
import time

import pytest
from httpx import HTTPError
from redis.asyncio import Redis
from redis.exceptions import RedisError

from core.app_settings import Settings
from core.security import OGWSAuthManager, TokenMetadata
from infrastructure.redis import get_redis_client
from tests.unit.api.test_token_setup import get_test_redis, get_test_settings


async def test_invalid_credentials():
    """Test token acquisition with invalid credentials."""
    settings = get_test_settings()
    # Override with invalid credentials
    settings.OGWS_CLIENT_ID = "invalid_id"
    settings.OGWS_CLIENT_SECRET = "invalid_secret"

    redis = await get_test_redis()

    try:
        auth_manager = OGWSAuthManager(settings, redis)
        with pytest.raises(HTTPError) as exc_info:
            await auth_manager.get_valid_token()
        assert exc_info.value.response.status_code == 401, "Expected 401 Unauthorized"
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
        assert token != "expired_token", "Should not reuse expired token"

        # Verify old token was removed
        metadata_exists = await redis.exists(auth_manager.token_metadata_key)
        assert metadata_exists, "New token metadata should exist"

        metadata = await auth_manager._get_token_metadata()
        assert metadata.token != "expired_token", "Expired token not replaced"

    finally:
        await redis.delete("ogws:auth:token")
        await redis.delete("ogws:auth:token:metadata")
        await redis.aclose()


async def test_token_validation_failure():
    """Test token validation failure handling."""
    settings = get_test_settings()
    redis = await get_test_redis()

    try:
        auth_manager = OGWSAuthManager(settings, redis)

        # Create an invalid auth header
        auth_header = {"Authorization": "Bearer invalid_token_here"}

        # Validate should return False for invalid token
        is_valid = await auth_manager.validate_token(auth_header)
        assert not is_valid, "Invalid token should fail validation"

        # Get token info should return None for invalid token
        token_info = await auth_manager.get_token_info()
        assert token_info is None, "Token info should be None for invalid token"

    finally:
        await redis.aclose()


if __name__ == "__main__":
    asyncio.run(test_expired_token())
