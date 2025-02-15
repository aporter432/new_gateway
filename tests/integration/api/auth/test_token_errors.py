"""Test token error handling.

Note on Redis cleanup:
We use redis.aclose() with type ignore comments to match the recommended cleanup
method from the Redis async client. The type hints don't yet include aclose(),
but it's preferred over the deprecated close() method.
"""

import asyncio
import time
from typing import cast

import pytest
from httpx import HTTPError, Request, Response
from unittest.mock import patch

from protocols.ogx.auth.manager import OGWSAuthManager, TokenMetadata
from tests.integration.api.auth.test_token_setup import get_test_redis, get_test_settings

# Use function-scoped event loop for better isolation
pytestmark = pytest.mark.asyncio

async def test_invalid_credentials():
    """Test token acquisition with invalid credentials."""
    settings = get_test_settings()
    settings.OGWS_CLIENT_ID = "invalid_id"
    settings.OGWS_CLIENT_SECRET = "invalid_secret"

    redis = await get_test_redis()
    try:
        auth_manager = OGWSAuthManager(settings, redis)
        mock_response = Response(
            status_code=401,
            json={"error": "invalid_credentials"},
            request=Request("POST", "http://proxy:8080/api/v1.0/token"),
        )
        
        with patch("httpx.AsyncClient.post", return_value=mock_response):
            with pytest.raises(HTTPError) as exc_info:
                await auth_manager.get_valid_token()
            assert exc_info.value.response is not None  # Type check
            assert exc_info.value.response.status_code == 401
    finally:
        await redis.aclose()  # type: ignore # Redis type hints don't include aclose


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
            created_at=now - 7200,
            expires_at=now - 3600,
            last_used=now - 3600,
        )
        await auth_manager._store_token_metadata(expired_metadata)

        # Mock the new token response
        mock_response = Response(200, json={"access_token": "new_token", "expires_in": 3600})

        with patch("httpx.AsyncClient.post", return_value=mock_response):
            token = await auth_manager.get_valid_token()
            assert token != "expired_token"

        metadata = await auth_manager._get_token_metadata()
        assert metadata.token != "expired_token"
    finally:
        await redis.aclose()  # type: ignore # Redis type hints don't include aclose


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
        await redis.aclose()  # type: ignore # Redis type hints don't include aclose


if __name__ == "__main__":
    asyncio.run(test_expired_token())
