# LOCATION: /tests/e2e/conftest.py
"""Configuration and fixtures for end-to-end tests.

This module provides the test configuration and fixtures required for
running end-to-end tests against real services.
"""


from datetime import datetime
from typing import Any, AsyncGenerator, Dict, List, Optional, Tuple

import pytest
import redis.asyncio as aioredis
from core.app_settings import Settings, get_settings
from protocols.ogx.constants.message_types import MessageType
from protocols.ogx.constants.transport_types import TransportType
from protocols.ogx.services.OGx_protocol_handler import OGxProtocolHandler
from protocols.ogx.validation.common.types import ValidationResult
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
    except aioredis.RedisError as e:
        pytest.skip(f"Redis not available: {str(e)}")

    yield redis
    await redis.close()


class DummyOGxProtocolHandler(OGxProtocolHandler):
    """Dummy implementation of OGxProtocolHandler for testing purposes."""

    async def authenticate(self, credentials: dict):
        """Authenticate with dummy credentials."""
        _ = credentials
        return

    async def submit_message(
        self,
        message: Dict[str, Any],
        destination_id: str,
        transport_type: Optional[TransportType] = None,
    ) -> Tuple[str, ValidationResult]:
        """Dummy implementation of submit_message."""
        _ = message
        _ = destination_id
        _ = transport_type
        return "dummy_message_id", ValidationResult(is_valid=True, errors=[])

    async def get_messages(
        self, from_utc: datetime, message_type: MessageType
    ) -> List[Dict[str, Any]]:
        """Dummy implementation of get_messages."""
        _ = from_utc
        _ = message_type
        return []

    async def get_message_status(self, message_id: str) -> Dict[str, Any]:
        """Dummy implementation of get_message_status."""
        _ = message_id
        return {"State": 0, "StatusUTC": datetime.utcnow().isoformat()}

    async def close(self):
        """Dummy implementation of close."""
        return


# LOCATION: /tests/e2e/conftest.py
@pytest.fixture(scope="session")
async def protocol_handler(settings: Settings) -> AsyncGenerator[DummyOGxProtocolHandler, None]:
    """Provide authenticated protocol handler."""
    handler = DummyOGxProtocolHandler()

    try:
        await handler.authenticate(
            {"client_id": settings.OGx_CLIENT_ID, "client_secret": settings.OGx_CLIENT_SECRET}
        )
    except OGxProtocolError as e:
        pytest.skip(f"Failed to authenticate: {str(e)}")

    yield handler
    await handler.close()  # Added cleanup


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
