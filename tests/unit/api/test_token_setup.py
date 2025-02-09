"""Test suite for OGWS token acquisition, validation, and lifecycle management."""

import asyncio
import time
from typing import Optional

from redis.asyncio import Redis

from core.app_settings import Settings
from core.security import OGWSAuthManager
from infrastructure.redis import get_redis_client


def get_test_settings() -> Settings:
    """Get settings configured for test environment."""
    return Settings(
        OGWS_CLIENT_ID="70000934",  # Test superuser account
        OGWS_CLIENT_SECRET="password",
        OGWS_BASE_URL="http://proxy:8080/api/v1.0",  # Use Docker service name and port
        OGWS_TEST_MODE=True,
        CUSTOMER_ID="test_customer",  # Required for logging
    )


async def get_test_redis() -> Redis:
    """Get Redis client for testing.

    Uses test DB to avoid conflicts with production.
    """
    return Redis(
        host="redis",  # Use Docker service name
        port=6379,
        db=15,  # Use test DB
        decode_responses=True,
    )


async def test_token_lifecycle():
    """Test complete token lifecycle including storage and metadata.

    This test verifies:
    1. Token acquisition and storage
    2. Token validation
    3. Metadata tracking (usage, validation counts)
    4. Token refresh conditions
    5. Token invalidation
    """
    settings = get_test_settings()
    redis = await get_test_redis()

    try:
        # Clear any existing test tokens
        await redis.delete("ogws:auth:token")
        await redis.delete("ogws:auth:token:metadata")

        auth_manager = OGWSAuthManager(settings, redis)

        print("\n=== Initial Token Acquisition ===")
        # Get initial token
        token = await auth_manager.get_valid_token()
        print(f"Token acquired: {bool(token)}")
        assert token is not None, "Failed to acquire token"

        # Get initial metadata
        initial_info = await auth_manager.get_token_info()
        print(f"Initial token info: {initial_info}")
        assert initial_info is not None, "Failed to get token metadata"
        assert initial_info["token"] == token[-8:], "Token mismatch in metadata"

        print("\n=== Token Validation ===")
        # Validate token
        auth_header = await auth_manager.get_auth_header()
        is_valid = await auth_manager.validate_token(auth_header)
        print(f"Token valid: {is_valid}")
        assert is_valid, "Token validation failed"

        # Check metadata after validation
        validation_info = await auth_manager.get_token_info()
        assert validation_info is not None, "Missing validation metadata"
        print(f"Validation count: {validation_info['validation_count']}")
        print(f"Last validated: {validation_info['last_validated']}")
        assert validation_info["validation_count"] > 0, "Validation count not updated"
        assert validation_info["last_validated"] is not None, "Last validated timestamp missing"

        print("\n=== Token Reuse ===")
        # Get token again (should reuse existing)
        reused_token = await auth_manager.get_valid_token()
        print(f"Token reused: {reused_token == token}")
        assert reused_token == token, "Token not reused as expected"

        # Check usage metadata
        usage_info = await auth_manager.get_token_info()
        assert usage_info is not None, "Missing usage metadata"
        print(f"Last used: {usage_info['last_used']}")
        assert (
            usage_info["last_used"] > initial_info["last_used"]
        ), "Last used timestamp not updated"

        print("\n=== Force Token Refresh ===")
        # Force token refresh
        new_token = await auth_manager.get_valid_token(force_refresh=True)
        print(f"Token still valid after force refresh: {new_token == token}")
        assert new_token is not None, "Failed to get valid token after force refresh"

        # Verify token is still valid
        auth_header = await auth_manager.get_auth_header()
        is_valid = await auth_manager.validate_token(auth_header)
        print(f"Token valid after refresh: {is_valid}")
        assert is_valid, "Token should still be valid after refresh"

        print("\n=== Token Invalidation ===")
        # Invalidate token
        await auth_manager.invalidate_token()

        # Verify token was removed
        metadata_exists = await redis.exists("ogws:auth:token:metadata")
        token_exists = await redis.exists("ogws:auth:token")
        print(f"Token metadata removed: {not metadata_exists}")
        print(f"Token removed: {not token_exists}")
        assert not metadata_exists, "Token metadata not removed"
        assert not token_exists, "Token not removed"

        # Get new token after invalidation
        final_token = await auth_manager.get_valid_token()
        print(f"New token acquired after invalidation: {bool(final_token)}")
        print(f"Final token different from original: {final_token != token}")
        assert final_token != token, "New token matches invalidated token"

    finally:
        # Clean up
        await redis.delete("ogws:auth:token")
        await redis.delete("ogws:auth:token:metadata")
        await redis.aclose()


if __name__ == "__main__":
    asyncio.run(test_token_lifecycle())
