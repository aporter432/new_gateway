# LOCATION: /tests/e2e/conftest.py
"""Configuration and fixtures for end-to-end tests.

This module provides the test configuration and fixtures required for
running end-to-end tests against real services.
"""

import asyncio

# LOCATION: /tests/conftest.py (ROOT)
import os
from datetime import datetime
from typing import AsyncGenerator, Generator

import pytest
import redis.asyncio as aioredis

from core.app_settings import Settings, get_settings
from protocols.ogx.services.ogws_protocol_handler import OGWSProtocolHandler
from protocols.ogx.validation.common.validation_exceptions import OGxProtocolError


def pytest_configure(config):
    """Configure pytest for e2e testing."""
    config.addinivalue_line("markers", "e2e: mark test as end-to-end test")
    config.addinivalue_line("markers", "external_api: mark test as requiring external API")
    config.addinivalue_line("markers", "requires_credentials: mark test as requiring credentials")
    config.addinivalue_line("markers", "slow: mark test as slow running")


# LOCATION: /tests/integration/conftest.py
@pytest.fixture(scope="session")
async def redis() -> AsyncGenerator[aioredis.Redis, None]:
    """Provide Redis connection for the test session."""
    settings = get_settings()
    redis = aioredis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=15,  # Use separate DB for e2e tests
        decode_responses=True,
    )
    try:
        await redis.ping()
    except Exception as e:
        pytest.skip(f"Redis not available: {str(e)}")

    yield redis
    await redis.close()


# LOCATION: /tests/e2e/conftest.py
@pytest.fixture(scope="session")
async def protocol_handler(settings: Settings) -> AsyncGenerator[OGWSProtocolHandler, None]:
    """Provide authenticated protocol handler."""
    handler = OGWSProtocolHandler()  # Will be replaced with real implementation

    try:
        await handler.authenticate(
            {"client_id": settings.OGWS_CLIENT_ID, "client_secret": settings.OGWS_CLIENT_SECRET}
        )
    except OGxProtocolError as e:
        pytest.skip(f"Failed to authenticate: {str(e)}")

    yield handler


# LOCATION: /tests/integration/conftest.py
@pytest.fixture(autouse=True)
async def cleanup_redis(redis: aioredis.Redis):
    """Clean up Redis test database before and after each test."""
    await redis.flushdb()
    yield
    await redis.flushdb()


# LOCATION: /tests/e2e/conftest.py
@pytest.fixture
def test_id() -> str:
    """Generate unique test identifier."""
    return f"e2e_test_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
