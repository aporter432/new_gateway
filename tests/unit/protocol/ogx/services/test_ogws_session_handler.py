"""Unit tests for OGWS SessionHandler implementation.

This module provides comprehensive testing of the OGWS session handler
according to OGWS-1.txt specifications. Each test class corresponds to a
specific method in the SessionHandler class, following Single
Responsibility Principle.

Test Organization:
    Tests are organized by method:
    - TestSessionHandlerInitialize: Tests initialize() method
    - TestSessionHandlerCreate: Tests create_session() method
    - TestSessionHandlerValidate: Tests validate_session() method
    - TestSessionHandlerEnd: Tests end_session() method
    - TestSessionHandlerRefresh: Tests refresh_session() method

Test Dependencies:
    - pytest: Test framework
    - pytest-asyncio: Async test support
    - pytest-mock: Mocking support
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch, ANY

import pytest
from redis.asyncio import Redis

from core.security import OGWSAuthManager
from protocols.ogx.services.ogws_session_handler import SessionHandler
from protocols.ogx.validation.common.validation_exceptions import (
    AuthenticationError,
    OGxProtocolError,
)


@pytest.fixture(autouse=True)
def mock_logger():
    """Mock logger for all tests."""
    with patch("protocols.ogx.services.ogws_session_handler.get_protocol_logger") as mock:
        logger = MagicMock()
        mock.return_value = logger
        yield logger


@pytest.fixture
def mock_redis():
    """Create mock Redis client."""
    redis = AsyncMock(spec=Redis)
    redis.hgetall = AsyncMock(return_value={})
    redis.hmset = AsyncMock()
    redis.hset = AsyncMock()
    redis.delete = AsyncMock()
    redis.expire = AsyncMock()
    redis.keys = AsyncMock(return_value=[])
    redis.exists = AsyncMock(return_value=True)
    return redis


@pytest.fixture
def mock_auth_manager():
    """Create mock OGWSAuthManager."""
    auth_manager = AsyncMock(spec=OGWSAuthManager)
    auth_manager.get_valid_token = AsyncMock(return_value="test_token")
    auth_manager.validate_token = AsyncMock(return_value=True)
    return auth_manager


@pytest.fixture
async def session_handler(mock_redis, mock_auth_manager):
    """Create initialized SessionHandler with mocked dependencies."""
    with patch(
        "protocols.ogx.services.ogws_session_handler.get_redis_client", return_value=mock_redis
    ):
        with patch(
            "protocols.ogx.services.ogws_session_handler.OGWSAuthManager",
            return_value=mock_auth_manager,
        ):
            handler = SessionHandler()
            await handler.initialize()
            return handler


@pytest.mark.asyncio
class TestSessionHandlerInitialize:
    """Test suite for SessionHandler.initialize method."""

    async def test_successful_initialization(self, mock_redis):
        """Test successful initialization."""
        with patch(
            "protocols.ogx.services.ogws_session_handler.get_redis_client", return_value=mock_redis
        ):
            handler = SessionHandler()
            await handler.initialize()
            assert handler.redis is not None
            assert handler.auth_manager is not None

    async def test_failed_initialization(self):
        """Test initialization with Redis connection failure."""
        with patch(
            "protocols.ogx.services.ogws_session_handler.get_redis_client", return_value=None
        ):
            handler = SessionHandler()
            with pytest.raises(RuntimeError) as exc:
                await handler.initialize()
            assert "Failed to initialize Redis connection" in str(exc.value)


@pytest.mark.asyncio
class TestSessionHandlerCreate:
    """Test suite for SessionHandler.create_session method."""

    @pytest.fixture
    def valid_credentials(self):
        """Create valid test credentials."""
        return {
            "client_id": "test_id",
            "client_secret": "test_secret",
        }

    async def test_successful_session_creation(
        self, session_handler, valid_credentials, mock_logger
    ):
        """Test successful session creation."""
        session_id = await session_handler.create_session(valid_credentials)
        assert isinstance(session_id, str)
        assert len(session_id) > 0
        mock_logger.info.assert_called_once()

    async def test_session_limit_exceeded(
        self, session_handler, valid_credentials, mock_redis, mock_logger
    ):
        """Test session creation when limit is exceeded."""
        mock_redis.keys.return_value = ["session1", "session2", "session3"]
        with pytest.raises(OGxProtocolError) as exc:
            await session_handler.create_session(valid_credentials)
        assert "Maximum concurrent sessions" in str(exc.value)
        mock_logger.error.assert_called_once()

    async def test_authentication_failure(
        self, session_handler, valid_credentials, mock_auth_manager, mock_logger
    ):
        """Test session creation with authentication failure."""
        mock_auth_manager.get_valid_token.side_effect = AuthenticationError("Invalid credentials")
        with pytest.raises(AuthenticationError):
            await session_handler.create_session(valid_credentials)
        mock_logger.error.assert_called_once()

    async def test_uninitialized_handler(self, mock_logger):
        """Test session creation with uninitialized handler."""
        handler = SessionHandler()
        with pytest.raises(RuntimeError) as exc:
            await handler.create_session({})
        assert "SessionHandler not initialized" in str(exc.value)


@pytest.mark.asyncio
class TestSessionHandlerValidate:
    """Test suite for SessionHandler.validate_session method."""

    async def test_valid_session(self, session_handler, mock_redis, mock_logger):
        """Test validation of valid session."""
        token = "test_token"
        session_data = {
            b"token": token.encode(),  # Redis returns bytes
            b"created_at": str(datetime.now()).encode(),
            b"last_activity": str(datetime.now()).encode(),
            b"request_count": b"0",
        }
        mock_redis.hgetall.return_value = session_data
        mock_redis.exists.return_value = True
        mock_redis.hset = AsyncMock()  # For last_activity update

        # Mock validate_token to return True for valid auth header
        async def validate_token_mock(auth_header):
            expected_header = {"Authorization": f"Bearer {token}"}
            return auth_header == expected_header

        session_handler.auth_manager.validate_token = validate_token_mock

        result = await session_handler.validate_session("test_session")
        assert result is True
        mock_logger.error.assert_not_called()
        mock_logger.warning.assert_not_called()
        mock_redis.hset.assert_called_once_with(
            f"{session_handler.session_key_prefix}test_session",
            "last_activity",
            ANY,  # Don't check exact timestamp
        )

    async def test_invalid_session(self, session_handler, mock_redis, mock_logger):
        """Test validation of invalid session."""
        mock_redis.hgetall.return_value = {}  # No session data
        mock_redis.exists.return_value = False
        mock_redis.hset = AsyncMock()  # Should not be called

        result = await session_handler.validate_session("invalid_session")
        assert result is False
        mock_logger.error.assert_not_called()
        mock_logger.warning.assert_not_called()
        mock_redis.hset.assert_not_called()  # No update for invalid session

    async def test_validation_error_handling(
        self, session_handler, mock_redis, mock_auth_manager, mock_logger
    ):
        """Test validation error handling."""
        session_data = {
            b"token": b"test_token",  # Redis returns bytes
            b"created_at": str(datetime.now()).encode(),
            b"last_activity": str(datetime.now()).encode(),
            b"request_count": b"0",
        }
        mock_redis.hgetall.return_value = session_data
        mock_redis.exists.return_value = True
        mock_redis.hset = AsyncMock()  # For last_activity update
        mock_auth_manager.validate_token.side_effect = Exception("Validation error")

        result = await session_handler.validate_session("test_session")
        assert result is False
        mock_logger.error.assert_called_once_with(
            "Token validation failed",
            extra={
                "customer_id": session_handler.settings.CUSTOMER_ID,
                "asset_id": "session_handler",
                "session_id": "test_session",
                "error": "Validation error",
                "action": "validate_session",
            },
        )
        mock_redis.hset.assert_called_once()  # Last activity still updated

    async def test_last_activity_update_error(self, session_handler, mock_redis, mock_logger):
        """Test handling of last activity update error."""
        token = "test_token"
        session_data = {
            b"token": token.encode(),
            b"created_at": str(datetime.now()).encode(),
            b"last_activity": str(datetime.now()).encode(),
            b"request_count": b"0",
        }
        mock_redis.hgetall.return_value = session_data
        mock_redis.exists.return_value = True
        mock_redis.hset.side_effect = Exception("Redis error")

        # Mock validate_token to return True
        session_handler.auth_manager.validate_token = AsyncMock(return_value=True)

        result = await session_handler.validate_session("test_session")
        assert result is True  # Should still validate despite update error
        mock_logger.error.assert_not_called()
        mock_logger.warning.assert_called_once_with(
            "Failed to update last activity",
            extra={
                "customer_id": session_handler.settings.CUSTOMER_ID,
                "asset_id": "session_handler",
                "session_id": "test_session",
                "error": "Redis error",
                "action": "validate_session",
            },
        )

    async def test_redis_failure_during_validation(self, session_handler, mock_redis, mock_logger):
        """Test Redis failure during session validation."""
        mock_redis.hgetall.side_effect = Exception("Redis connection error")
        result = await session_handler.validate_session("test_session")
        assert result is False
        mock_logger.error.assert_not_called()  # Should not log for Redis failures without session data

    async def test_redis_failure_with_existing_session(
        self, session_handler, mock_redis, mock_logger
    ):
        """Test Redis failure with existing session data."""
        # First call succeeds and returns session data
        mock_redis.hgetall.return_value = {
            b"token": b"test_token",
            b"created_at": str(datetime.now()).encode(),
        }
        # Second call (validation) fails
        session_handler.auth_manager.validate_token.side_effect = Exception(
            "Redis error during validation"
        )

        result = await session_handler.validate_session("test_session")
        assert result is False
        mock_logger.error.assert_called_once_with(
            "Token validation failed",
            extra={
                "customer_id": session_handler.settings.CUSTOMER_ID,
                "asset_id": "session_handler",
                "session_id": "test_session",
                "error": "Redis error during validation",
                "action": "validate_session",
            },
        )


@pytest.mark.asyncio
class TestSessionHandlerEnd:
    """Test suite for SessionHandler.end_session method."""

    async def test_successful_session_end(self, session_handler, mock_logger):
        """Test successful session termination."""
        await session_handler.end_session("test_session")
        session_handler.redis.delete.assert_called_once()
        mock_logger.info.assert_called_once()

    async def test_session_end_error(self, session_handler, mock_redis, mock_logger):
        """Test session termination with error."""
        mock_redis.delete.side_effect = Exception("Delete error")
        with pytest.raises(OGxProtocolError) as exc:
            await session_handler.end_session("test_session")
        assert "Failed to end session" in str(exc.value)
        mock_logger.error.assert_called_once()

    async def test_uninitialized_handler_end_session(self):
        """Test end_session with uninitialized handler."""
        handler = SessionHandler()
        with pytest.raises(RuntimeError) as exc:
            await handler.end_session("test_session")
        assert "SessionHandler not initialized" in str(exc.value)


@pytest.mark.asyncio
class TestSessionHandlerRefresh:
    """Test suite for SessionHandler.refresh_session method."""

    async def test_successful_refresh(self, session_handler, mock_logger):
        """Test successful session refresh."""
        await session_handler.refresh_session("test_session")
        session_handler.redis.hset.assert_called()
        mock_logger.info.assert_called_once()

    async def test_refresh_with_auth_error(self, session_handler, mock_auth_manager, mock_logger):
        """Test refresh with authentication error."""
        mock_auth_manager.get_valid_token.side_effect = AuthenticationError("Token refresh failed")
        with pytest.raises(OGxProtocolError) as exc:
            await session_handler.refresh_session("test_session")
        assert "Failed to refresh session" in str(exc.value)
        mock_logger.error.assert_called_once()

    async def test_refresh_with_redis_error(self, session_handler, mock_redis, mock_logger):
        """Test refresh with Redis error."""
        mock_redis.hset.side_effect = Exception("Redis error")
        with pytest.raises(OGxProtocolError) as exc:
            await session_handler.refresh_session("test_session")
        assert "Failed to refresh session" in str(exc.value)
        mock_logger.error.assert_called_once()

    async def test_uninitialized_handler_refresh_session(self):
        """Test refresh_session with uninitialized handler."""
        handler = SessionHandler()
        with pytest.raises(RuntimeError) as exc:
            await handler.refresh_session("test_session")
        assert "SessionHandler not initialized" in str(exc.value)
