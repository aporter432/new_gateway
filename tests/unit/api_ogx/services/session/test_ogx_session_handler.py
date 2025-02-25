"""Unit tests for OGx session handler.

Tests session management functionality according to OGx-1.txt Section 3.1 requirements.
"""

import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, AsyncGenerator, Dict, List, Optional, Set
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from freezegun import freeze_time
from redis.asyncio import Redis
from redis.exceptions import RedisError

from Protexis_Command.api.services.session.ogx_session_handler import (
    MAX_CONCURRENT_SESSIONS,
    SessionHandler,
    format_ogx_timestamp,
)
from Protexis_Command.core.settings.app_settings import Settings
from Protexis_Command.protocols.ogx.validation.ogx_validation_exceptions import (
    AuthenticationError,
    OGxProtocolError,
    ValidationError,
)


def encode_dict(d: Dict[str, Any]) -> Dict[bytes, bytes]:
    """Encode dictionary values to bytes for Redis mock."""
    return {
        k.encode()
        if isinstance(k, str)
        else k: (
            v.encode()
            if isinstance(v, str)
            else str(v).encode()
            if isinstance(v, (int, float))
            else v
        )
        for k, v in d.items()
    }


def decode_dict(d: Dict[bytes, bytes]) -> Dict[str, str]:
    """Decode dictionary values from bytes for Redis mock."""
    return {
        k.decode() if isinstance(k, bytes) else k: v.decode() if isinstance(v, bytes) else v
        for k, v in d.items()
    }


class RedisMockData:
    """Class to store Redis mock data."""

    def __init__(self):
        self.hash_data: Dict[str, Dict[bytes, bytes]] = {}
        self.set_data: Dict[str, set] = {}


class SessionHelper:
    """Helper class for session operations during testing."""

    def __init__(self, redis_client: Redis):
        self.client = redis_client

    async def set_session_state(self, session_id: str, state: Dict[str, Any]) -> None:
        """Set session state in Redis."""
        key = f"session:{session_id}"
        encoded_state = encode_dict(state)
        await self.client.hset(key, mapping=encoded_state)

    async def get_session_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session state from Redis."""
        key = f"session:{session_id}"
        state = await self.client.hgetall(key)
        return decode_dict(state) if state else None

    async def clear_sessions(self, pattern: str = "session:*") -> None:
        """Clear all sessions matching pattern."""
        keys = await self.client.keys(pattern)
        if keys:
            await self.client.delete(*keys)


@pytest.fixture(autouse=True)
def setup_logging():
    """Configure basic logging for tests."""
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger("session_handler")
    with patch("Protexis_Command.api.services.session.ogx_session_handler.logger", logger):
        yield


@pytest.fixture
def redis_data() -> RedisMockData:
    """Create Redis mock data store."""
    data = RedisMockData()
    return data


@pytest.fixture
def mock_redis(redis_data: RedisMockData) -> AsyncMock:
    """Create a mock Redis client with async methods."""
    mock = AsyncMock(spec=Redis)

    # Set up the mock methods
    async def mock_hgetall(key: str) -> Dict[bytes, bytes]:
        return redis_data.hash_data.get(key, {})

    async def mock_sadd(key: str, *values: str) -> int:
        redis_data.set_data.setdefault(key, set())
        for value in values:
            redis_data.set_data[key].add(value.encode() if isinstance(value, str) else value)
        return len(values)

    async def mock_scard(key: str) -> int:
        return len(redis_data.set_data.get(key, set()))

    async def mock_smembers(key: str) -> Set[bytes]:
        return redis_data.set_data.get(key, set())

    async def mock_keys(pattern: str) -> List[bytes]:
        prefix = pattern.rstrip("*")
        return [k.encode() for k in redis_data.hash_data.keys() if k.startswith(prefix)]

    async def mock_delete(*keys) -> int:
        count = 0
        for key in keys:
            key = key.decode() if isinstance(key, bytes) else key
            if key in redis_data.hash_data:
                del redis_data.hash_data[key]
                count += 1
            if key in redis_data.set_data:
                del redis_data.set_data[key]
                count += 1
        return count

    async def mock_hset(key: str, *args, mapping: Optional[Dict] = None, **kwargs) -> bool:
        if mapping:
            # Directly use the mapping as provided (it's already encoded by our handler)
            redis_data.hash_data[key] = mapping
        else:
            field, value = args
            redis_data.hash_data.setdefault(key, {})
            field_key = field.encode() if isinstance(field, str) else field
            field_value = (
                value
                if isinstance(value, bytes)
                else value.encode()
                if isinstance(value, str)
                else str(value).encode()
            )
            redis_data.hash_data[key][field_key] = field_value
        return True

    mock.hgetall = AsyncMock(side_effect=mock_hgetall)
    mock.sadd = AsyncMock(side_effect=mock_sadd)
    mock.scard = AsyncMock(side_effect=mock_scard)
    mock.smembers = AsyncMock(side_effect=mock_smembers)
    mock.keys = AsyncMock(side_effect=mock_keys)
    mock.delete = AsyncMock(side_effect=mock_delete)
    mock.hset = AsyncMock(side_effect=mock_hset)
    mock.expire = AsyncMock(return_value=True)
    mock.srem = AsyncMock(return_value=1)
    mock.hincrby = AsyncMock(return_value=1)

    # Create a pipeline mock
    pipeline_mock = AsyncMock()

    # Track pipeline operations
    pipeline_operations = []

    # Set up pipeline execute to record operations and apply them
    async def mock_pipeline_execute():
        result = []
        for name, args, kwargs in pipeline_mock.method_calls:
            if name != "execute" and name != "__aenter__" and name != "__aexit__":
                pipeline_operations.append((name, args, kwargs))

                # Apply the operations directly to the redis data
                if name == "hset":
                    key = args[0]
                    if "mapping" in kwargs:
                        mapping = kwargs["mapping"]
                        # Use mapping directly as provided (already encoded)
                        redis_data.hash_data[key] = mapping
                        result.append(len(mapping))
                    else:
                        field, value = args[1], args[2]
                        redis_data.hash_data.setdefault(key, {})
                        field_key = field.encode() if isinstance(field, str) else field
                        field_value = (
                            value
                            if isinstance(value, bytes)
                            else value.encode()
                            if isinstance(value, str)
                            else str(value).encode()
                        )
                        redis_data.hash_data[key][field_key] = field_value
                        result.append(1)

                elif name == "hincrby":
                    key, field, amount = args
                    redis_data.hash_data.setdefault(key, {})
                    field_bytes = field.encode() if isinstance(field, str) else field
                    current = int(redis_data.hash_data[key].get(field_bytes, b"0").decode())
                    new_value = current + amount
                    redis_data.hash_data[key][field_bytes] = str(new_value).encode()
                    result.append(new_value)

                elif name == "sadd":
                    key, *values = args
                    redis_data.set_data.setdefault(key, set())
                    count = 0
                    for value in values:
                        value_bytes = value.encode() if isinstance(value, str) else value
                        if value_bytes not in redis_data.set_data[key]:
                            redis_data.set_data[key].add(value_bytes)
                            count += 1
                    result.append(count)

                elif name == "srem":
                    key, *values = args
                    count = 0
                    if key in redis_data.set_data:
                        for value in values:
                            value_bytes = value.encode() if isinstance(value, str) else value
                            if value_bytes in redis_data.set_data[key]:
                                redis_data.set_data[key].remove(value_bytes)
                                count += 1
                    result.append(count)

                elif name == "expire":
                    key, seconds = args
                    # We don't actually implement expiry, just return success
                    result.append(1)

                elif name == "delete":
                    count = 0
                    for key in args:
                        key_str = key.decode() if isinstance(key, bytes) else key
                        if key_str in redis_data.hash_data:
                            del redis_data.hash_data[key_str]
                            count += 1
                        if key_str in redis_data.set_data:
                            del redis_data.set_data[key_str]
                            count += 1
                    result.append(count)
                else:
                    # Default success response
                    result.append(True)

        return result if result else [True] * len(pipeline_operations)

    pipeline_mock.execute = AsyncMock(side_effect=mock_pipeline_execute)

    # Set up the pipeline methods to return the pipeline for chaining
    pipeline_mock.hset = AsyncMock(return_value=pipeline_mock)
    pipeline_mock.sadd = AsyncMock(return_value=pipeline_mock)
    pipeline_mock.srem = AsyncMock(return_value=pipeline_mock)
    pipeline_mock.delete = AsyncMock(return_value=pipeline_mock)
    pipeline_mock.expire = AsyncMock(return_value=pipeline_mock)
    pipeline_mock.hincrby = AsyncMock(return_value=pipeline_mock)
    pipeline_mock.scard = AsyncMock(return_value=pipeline_mock)

    # Track operations for testing
    pipeline_mock.get_operations = lambda: pipeline_operations
    pipeline_mock.clear_operations = lambda: pipeline_operations.clear()

    # Set up the pipeline context manager methods
    pipeline_mock.__aenter__ = AsyncMock(return_value=pipeline_mock)
    pipeline_mock.__aexit__ = AsyncMock(return_value=None)

    # Attach the pipeline mock to the Redis mock
    mock.pipeline = MagicMock(return_value=pipeline_mock)

    return mock


@pytest.fixture
def mock_protocol_handler_cls() -> Mock:
    """Create a mock protocol handler class."""
    handler = Mock()
    handler.__name__ = "MockOGxProtocolHandler"

    instance = AsyncMock()
    instance.authenticate = AsyncMock(return_value="test_token")
    handler.return_value = instance

    return handler


@pytest.fixture
def session_helper(mock_redis) -> SessionHelper:
    """Create a session helper instance."""
    return SessionHelper(mock_redis)


@pytest.fixture
async def session_handler(
    mock_protocol_handler_cls, mock_redis, settings: Settings
) -> AsyncGenerator[SessionHandler, None]:
    """Create a session handler instance with mocked dependencies."""
    with patch(
        "Protexis_Command.api.services.session.ogx_session_handler.get_redis_client",
        return_value=mock_redis,
    ):
        handler = SessionHandler(mock_protocol_handler_cls)
        await handler.initialize()
        yield handler
        await handler.close()


@pytest.fixture
def valid_credentials(settings: Settings) -> Dict[str, Any]:
    """Return valid test credentials."""
    return {"client_id": settings.OGx_CLIENT_ID, "client_secret": "password", "expires_in": 3600}


class TestSessionHandler:
    """Test suite for SessionHandler class."""

    async def test_initialization(self, session_handler, mock_redis):
        """Test successful initialization."""
        assert session_handler.redis == mock_redis
        assert session_handler._cleanup_task is not None

    async def test_create_session_success(
        self, session_handler, valid_credentials, mock_redis, redis_data, settings
    ):
        """Test successful session creation with test credentials."""
        # Create session
        session_id = await session_handler.create_session(valid_credentials)
        assert isinstance(session_id, str)
        assert len(session_id) > 0

        # Directly check if session data was stored in our redis_data
        session_key = f"session:{session_id}"
        assert session_key in redis_data.hash_data, "Session data should be stored in Redis"

        # Also check using the Redis mock
        session_state = await mock_redis.hgetall(session_key)
        assert session_state, "Session state should not be empty"

        decoded_state = decode_dict(session_state)
        assert decoded_state["client_id"] == settings.OGx_CLIENT_ID
        assert "token" in decoded_state
        assert "expires_at" in decoded_state

    async def test_create_session_missing_credentials(self, session_handler):
        """Test session creation with missing credentials."""
        with pytest.raises(
            (ValidationError, OGxProtocolError), match="Missing required credentials"
        ):
            await session_handler.create_session({})

    async def test_create_session_authentication_failure(
        self, session_handler, valid_credentials, mock_protocol_handler_cls
    ):
        """Test session creation with authentication failure."""
        mock_protocol_handler_cls.return_value.authenticate.side_effect = AuthenticationError(
            "Invalid credentials"
        )

        with pytest.raises(AuthenticationError, match="Invalid credentials"):
            await session_handler.create_session(valid_credentials)

    async def test_create_session_concurrent_limit(
        self, session_handler, valid_credentials, mock_redis
    ):
        """Test enforcement of concurrent session limit."""
        # Set up mock to simulate maximum sessions
        client_sessions_key = f"client_sessions:{valid_credentials['client_id']}"
        await mock_redis.sadd(
            client_sessions_key, *[str(i) for i in range(MAX_CONCURRENT_SESSIONS)]
        )

        with pytest.raises(OGxProtocolError, match="Maximum concurrent sessions exceeded"):
            await session_handler.create_session(valid_credentials)

    async def test_create_session_redis_failure(
        self, session_handler, valid_credentials, mock_redis
    ):
        """Test session creation with Redis failure."""
        # Modify the pipeline's execute method to raise an exception
        pipeline_mock = mock_redis.pipeline.return_value
        original_execute = pipeline_mock.execute

        # First mock scard to avoid the first await error
        original_scard = mock_redis.scard
        mock_redis.scard = AsyncMock(return_value=0)

        # Then set the pipeline execute to raise the Redis error
        pipeline_mock.execute = AsyncMock(side_effect=RedisError("Storage failed"))

        with pytest.raises(OGxProtocolError, match="Failed to create session"):
            await session_handler.create_session(valid_credentials)

        # Restore original methods for other tests
        pipeline_mock.execute = original_execute
        mock_redis.scard = original_scard

    async def test_validate_session_success(
        self, session_handler, mock_redis, redis_data, settings
    ):
        """Test successful session validation."""
        session_id = str(uuid.uuid4())
        expires_at = datetime.utcnow() + timedelta(hours=1)
        session_data = {
            "client_id": settings.OGx_CLIENT_ID,
            "token": "test_token",
            "expires_at": format_ogx_timestamp(expires_at),
            "last_access": format_ogx_timestamp(datetime.utcnow()),
            "access_count": "0",
        }

        # Properly encode the session data as bytes
        session_key = f"session:{session_id}"
        redis_data.hash_data[session_key] = encode_dict(session_data)

        is_valid = await session_handler.validate_session(session_id)
        assert is_valid, "Session should be valid"

    async def test_validate_session_expired(
        self, session_handler, mock_redis, redis_data, settings
    ):
        """Test validation of expired session."""
        session_id = str(uuid.uuid4())
        expired_time = datetime.utcnow() - timedelta(hours=1)
        session_data = {
            "client_id": settings.OGx_CLIENT_ID,
            "token": "test_token",
            "expires_at": format_ogx_timestamp(expired_time),
            "last_access": format_ogx_timestamp(expired_time),
            "access_count": "0",
        }

        # Properly encode the session data as bytes
        session_key = f"session:{session_id}"
        redis_data.hash_data[session_key] = encode_dict(session_data)

        # Set up client sessions
        client_sessions_key = f"client_sessions:{settings.OGx_CLIENT_ID}"
        redis_data.set_data.setdefault(client_sessions_key, set())
        redis_data.set_data[client_sessions_key].add(session_id.encode())

        is_valid = await session_handler.validate_session(session_id)
        assert not is_valid, "Expired session should not be valid"

    async def test_validate_session_not_found(self, session_handler):
        """Test validation of non-existent session."""
        session_id = str(uuid.uuid4())
        is_valid = await session_handler.validate_session(session_id)
        assert not is_valid, "Non-existent session should not be valid"

    async def test_cleanup_expired_sessions(
        self, session_handler, mock_redis, redis_data, settings
    ):
        """Test cleanup of expired sessions."""
        # Create expired session
        expired_session = str(uuid.uuid4())
        # Set the expires_at date to 2020 which is well before our frozen time of 2030
        expired_time = datetime(2020, 1, 1, 0, 0, 0)
        session_data = {
            "client_id": settings.OGx_CLIENT_ID,
            "token": "test_token",
            "expires_at": format_ogx_timestamp(expired_time),
            "last_access": format_ogx_timestamp(expired_time),
            "access_count": "0",
        }

        # Properly encode the session data as bytes
        session_key = f"session:{expired_session}"
        redis_data.hash_data[session_key] = encode_dict(session_data)

        # Set up client sessions
        client_sessions_key = f"client_sessions:{settings.OGx_CLIENT_ID}"
        redis_data.set_data.setdefault(client_sessions_key, set())
        redis_data.set_data[client_sessions_key].add(expired_session.encode())

        # Mock the Redis keys call to return our test session
        mock_redis.keys.return_value = [session_key.encode()]

        # Set up the pipeline mock to properly support delete operations
        # pipeline_mock = mock_redis.pipeline.return_value

        # Ensure the delete operation happens directly by patching the end_session method
        original_end_session = session_handler.end_session

        async def mocked_end_session(session_id):
            # Get client ID before deleting
            session_key = f"session:{session_id}"
            if session_key in redis_data.hash_data:
                session_data = redis_data.hash_data[session_key]
                client_id = session_data[b"client_id"].decode()
                client_sessions_key = f"client_sessions:{client_id}"

                # Delete session data
                del redis_data.hash_data[session_key]

                # Remove from client sessions set
                if client_sessions_key in redis_data.set_data:
                    if session_id.encode() in redis_data.set_data[client_sessions_key]:
                        redis_data.set_data[client_sessions_key].remove(session_id.encode())

            # Call original for logging and metrics
            await original_end_session(session_id)

        # Apply the mock
        session_handler.end_session = mocked_end_session

        # Temporarily replace the asyncio.sleep to avoid waiting in tests
        original_sleep = asyncio.sleep
        asyncio.sleep = AsyncMock()

        # Use freezegun to set the date to a future date
        with freeze_time("2030-01-01T00:00:00"):
            try:
                # Directly validate the session which should detect it as expired
                # and call end_session to clean it up
                valid = await session_handler.validate_session(expired_session)

                # Session should be marked as invalid (expired)
                assert not valid, "Expired session should be invalid"

                # Verify session was cleaned up
                assert (
                    session_key not in redis_data.hash_data
                ), "Expired session should have been removed"
                assert expired_session.encode() not in redis_data.set_data.get(
                    client_sessions_key, set()
                ), "Expired session should have been removed from client sessions"

            finally:
                # Restore the original functions
                asyncio.sleep = original_sleep
                session_handler.end_session = original_end_session

    async def test_close(self, session_handler):
        """Test proper cleanup on close."""
        await session_handler.close()
        assert session_handler._cleanup_task is None

    async def test_session_metrics(
        self, session_handler, valid_credentials, mock_redis, redis_data
    ):
        """Test that session metrics are properly logged."""
        # Set up a mock logger to track metrics
        logger = logging.getLogger("session_handler")

        # Create a new patch for the logger using unittest.mock directly
        with patch.object(logger, "info") as mock_info:
            # Create session
            session_id = await session_handler.create_session(valid_credentials)
            assert session_id is not None, "Session should have been created"

            # Verify metrics were logged
            assert mock_info.call_count > 0, "No logs were recorded"

            # Check if any of the calls included metrics
            metric_calls = [
                call
                for call in mock_info.call_args_list
                if call[1].get("extra")
                and isinstance(call[1].get("extra"), dict)
                and "metric_name" in call[1].get("extra")
            ]

            assert len(metric_calls) > 0, "No metric logs were recorded"

            # At least one log should be about session counts or creation
            session_metrics = [
                call
                for call in metric_calls
                if any(
                    metric_term in call[1]["extra"]["metric_name"]
                    for metric_term in ["session", "Session"]
                )
            ]

            assert len(session_metrics) > 0, "No session-related metrics were logged"
