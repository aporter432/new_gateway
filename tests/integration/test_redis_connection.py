"""Integration tests for Redis connectivity.

This module tests the basic Redis connection and operations
to verify our integration test environment is working correctly.
"""

import pytest
import redis.asyncio as aioredis

from Protexis_Command.core.app_settings import get_settings


@pytest.mark.asyncio
async def test_redis_connection():
    """Test basic Redis connectivity."""
    settings = get_settings()
    redis = aioredis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB,
        decode_responses=True,
    )

    try:
        # Test connection
        await redis.ping()

        # Test basic operations
        await redis.set("test_key", "test_value")
        value = await redis.get("test_key")
        assert value == "test_value"

        # Test deletion
        await redis.delete("test_key")
        value = await redis.get("test_key")
        assert value is None

    finally:
        await redis.aclose()


@pytest.mark.asyncio
async def test_redis_pubsub():
    """Test Redis pub/sub functionality."""
    settings = get_settings()
    redis = aioredis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB,
        decode_responses=True,
    )

    try:
        # Create pubsub instance
        pubsub = redis.pubsub()
        await pubsub.subscribe("test_channel")

        # Publish a message
        await redis.publish("test_channel", "test_message")

        # Get the message
        message = await pubsub.get_message(timeout=1)
        # First message is subscription confirmation
        assert message["type"] == "subscribe"

        # Get the actual message
        message = await pubsub.get_message(timeout=1)
        assert message["type"] == "message"
        assert message["data"] == "test_message"

    finally:
        await pubsub.close()
        await redis.aclose()
