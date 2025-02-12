"""Configuration and fixtures for end-to-end tests.

This module provides the test configuration and fixtures required for
running end-to-end tests against real services.
"""

import os
import pytest
import asyncio
from typing import AsyncGenerator, Generator
import redis.asyncio as aioredis
from datetime import datetime

from core.app_settings import Settings, get_settings
from protocols.ogx.services.ogws_protocol_handler import OGWSProtocolHandler
from protocols.ogx.validation.common.validation_exceptions import OGxProtocolError


def pytest_configure(config):
    """Configure pytest for e2e testing."""
    # Register e2e markers
    config.addinivalue_line("markers", "e2e: mark test as end-to-end test")
    config.addinivalue_line("markers", "external_api: mark test as requiring external API")
    config.addinivalue_line("markers", "requires_credentials: mark test as requiring credentials")
    config.addinivalue_line("markers", "slow: mark test as slow running")


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def settings() -> Settings:
    """Provide test settings with validation."""
    settings = get_settings()

    # Validate required settings
    missing = []
    if not settings.OGWS_CLIENT_ID:
        missing.append("OGWS_CLIENT_ID")
    if not settings.OGWS_CLIENT_SECRET:
        missing.append("OGWS_CLIENT_SECRET")
    if not settings.OGWS_TEST_MOBILE_ID:
        missing.append("OGWS_TEST_MOBILE_ID")

    if missing:
        pytest.skip(f"Missing required settings: {', '.join(missing)}")

    return settings


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


@pytest.fixture(autouse=True)
async def cleanup_redis(redis: aioredis.Redis):
    """Clean up Redis test database before and after each test."""
    await redis.flushdb()
    yield
    await redis.flushdb()


@pytest.fixture
def test_id() -> str:
    """Generate unique test identifier."""
    return f"e2e_test_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
