"""Shared test fixtures and configuration.

This module provides pytest fixtures shared across test modules:
1. Redis mocks
2. Settings configuration
3. Logging setup
4. Common test data
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from redis.asyncio import Redis
from core.app_settings import Settings
from core.logging.loggers import get_infra_logger


@pytest.fixture(autouse=True)
def mock_logger():
    """Mock logger to prevent actual logging during tests."""
    with MagicMock() as mock:
        yield mock


@pytest.fixture
def test_settings():
    """Test settings with mock values."""
    return Settings(
        OGWS_CLIENT_ID="test_client",
        OGWS_CLIENT_SECRET="test_secret",
        CUSTOMER_ID="test_customer",
        REDIS_HOST="localhost",
        REDIS_PORT=6379,
        REDIS_DB=15,  # Use test DB
    )


@pytest.fixture
async def mock_redis():
    """Mock Redis client for testing."""
    redis = AsyncMock(spec=Redis)
    # Setup basic Redis operations
    redis.hset = AsyncMock()
    redis.hget = AsyncMock()
    redis.hdel = AsyncMock()
    redis.hgetall = AsyncMock(return_value={})
    redis.exists = AsyncMock(return_value=False)
    redis.delete = AsyncMock()

    # Setup pipeline
    pipeline = AsyncMock()
    pipeline.hdel = AsyncMock()
    pipeline.hset = AsyncMock()
    pipeline.execute = AsyncMock()
    redis.pipeline = MagicMock()
    redis.pipeline.return_value.__aenter__.return_value = pipeline
    redis.pipeline.return_value.__aexit__ = AsyncMock()

    return redis


@pytest.fixture
def sample_message_payload():
    """Sample message payload for testing."""
    return {
        "DestinationID": "TEST-001",
        "Payload": {
            "Name": "test_message",
            "Fields": [
                {"Name": "field1", "Value": "test1"},
                {"Name": "field2", "Value": 123},
            ],
        },
    }
