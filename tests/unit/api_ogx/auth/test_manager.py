"""Unit tests for OGx authentication manager."""

import json
import time
from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest
from redis.exceptions import RedisError

from Protexis_Command.api.common.auth.manager import OGxAuthManager, TokenMetadata
from Protexis_Command.core.settings.app_settings import Settings
from Protexis_Command.protocols.ogx.validation.ogx_validation_exceptions import OGxProtocolError


@pytest.fixture
def mock_settings():
    """Create mock settings for testing."""
    settings = Mock(spec=Settings)
    settings.OGx_BASE_URL = "http://test.com/api"
    settings.OGx_CLIENT_ID = "test_client"
    settings.OGx_CLIENT_SECRET = "test_secret"
    settings.CUSTOMER_ID = "test_customer"
    return settings


@pytest.fixture
def mock_redis():
    """Create mock Redis client."""
    redis = AsyncMock()
    redis.get.return_value = None
    return redis


@pytest.fixture
def mock_logger():
    """Create mock logger."""
    return Mock()


@pytest.fixture
def auth_manager(mock_settings, mock_redis, mock_logger):
    """Create OGxAuthManager instance with mocked dependencies."""
    manager = OGxAuthManager(settings=mock_settings, redis=mock_redis)
    manager.logger = mock_logger
    return manager


@pytest.fixture
def mock_token_metadata():
    """Create sample token metadata."""
    now = time.time()
    return TokenMetadata(
        token="test_token",
        created_at=now,
        expires_at=now + 3600,  # 1 hour expiry
        last_used=now,
        last_validated=now,
        validation_count=0,
    )


@pytest.mark.unit
class TestTokenMetadata:
    """Test TokenMetadata class functionality."""

    def test_to_dict(self, mock_token_metadata):
        """Test conversion to dictionary."""
        data = mock_token_metadata.to_dict()
        assert data["token"] == "test_token"
        assert isinstance(data["created_at"], float)
        assert isinstance(data["expires_at"], float)

    def test_from_dict(self):
        """Test creation from dictionary."""
        now = time.time()
        data = {
            "token": "test_token",
            "created_at": now,
            "expires_at": now + 3600,
            "last_used": now,
            "last_validated": now,
            "validation_count": 0,
        }
        metadata = TokenMetadata.from_dict(data)
        assert metadata.token == "test_token"
        assert metadata.created_at == now


@pytest.mark.unit
class TestOGxAuthManager:
    """Test OGxAuthManager class functionality."""

    @pytest.mark.asyncio
    async def test_get_valid_token_cached(self, auth_manager, mock_redis, mock_token_metadata):
        """Test getting a cached valid token."""
        # Setup mock Redis to return valid token metadata
        mock_redis.get.return_value = json.dumps(mock_token_metadata.to_dict())

        # Mock _is_token_expiring_soon to return False
        with patch.object(auth_manager, "_is_token_expiring_soon", return_value=False):
            token = await auth_manager.get_valid_token()
            assert token == "test_token"
            mock_redis.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_valid_token_expired(self, auth_manager, mock_redis, mock_token_metadata):
        """Test getting a new token when cached token is expired."""
        mock_redis.get.return_value = json.dumps(mock_token_metadata.to_dict())

        # Mock token as expired
        with patch.object(auth_manager, "_is_token_expiring_soon", return_value=True), patch.object(
            auth_manager, "_acquire_new_token", return_value="new_token"
        ):
            token = await auth_manager.get_valid_token()
            assert token == "new_token"

    @pytest.mark.asyncio
    async def test_get_auth_header_success(self, auth_manager, mocker):
        """Test getting authorization header."""
        mocker.patch.object(auth_manager, "get_valid_token", return_value="test_token")
        header = await auth_manager.get_auth_header()
        assert header == {"Authorization": "Bearer test_token"}

    @pytest.mark.asyncio
    async def test_get_auth_header_failure(self, auth_manager, mocker):
        """Test authorization header failure."""
        mocker.patch.object(auth_manager, "get_valid_token", side_effect=Exception("Token error"))
        with pytest.raises(OGxProtocolError):
            await auth_manager.get_auth_header()

    @pytest.mark.asyncio
    async def test_validate_token_success(self, auth_manager, mocker):
        """Test successful token validation."""
        mock_response = Mock()
        mock_response.status_code = 200

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_client
            result = await auth_manager.validate_token({"Authorization": "Bearer test_token"})
            assert result is True

    @pytest.mark.asyncio
    async def test_validate_token_invalid(self, auth_manager, mocker):
        """Test invalid token validation."""
        mock_response = Mock()
        mock_response.status_code = 401

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_client
            result = await auth_manager.validate_token({"Authorization": "Bearer test_token"})
            assert result is False

    @pytest.mark.asyncio
    async def test_invalidate_token(self, auth_manager, mock_redis):
        """Test token invalidation."""
        await auth_manager.invalidate_token()
        assert mock_redis.delete.call_count == 2

    @pytest.mark.asyncio
    async def test_redis_storage_failure(self, auth_manager, mock_redis, mock_logger):
        """Test handling of Redis storage failures."""
        mock_redis.setex.side_effect = RedisError("Storage failed")
        metadata = TokenMetadata(
            token="test_token",
            created_at=time.time(),
            expires_at=time.time() + 3600,
            last_used=time.time(),
        )
        await auth_manager._store_token_metadata(metadata)
        mock_logger.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_token_info(self, auth_manager, mock_redis, mock_token_metadata):
        """Test getting token info."""
        mock_redis.get.return_value = json.dumps(mock_token_metadata.to_dict())
        info = await auth_manager.get_token_info()
        assert info is not None
        assert info["token"] == mock_token_metadata.token[-8:]
        assert "ttl" in info

    @pytest.mark.asyncio
    async def test_acquire_new_token(self, auth_manager, mocker):
        """Test acquiring new token."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"access_token": "new_token", "expires_in": 3600}

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_client
            token = await auth_manager._acquire_new_token()
            assert token == "new_token"

    @pytest.mark.asyncio
    async def test_get_token_metadata_json_error(self, auth_manager, mock_redis):
        """Test handling of invalid JSON in Redis."""
        mock_redis.get.return_value = "invalid json"
        metadata = await auth_manager._get_token_metadata()
        assert metadata is None

    @pytest.mark.asyncio
    async def test_validate_token_http_error(self, auth_manager, mocker):
        """Test validation when HTTP request fails."""
        mock_client = AsyncMock()
        mock_client.get.side_effect = httpx.HTTPError("Connection failed")

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_client
            result = await auth_manager.validate_token({"Authorization": "Bearer test_token"})
            assert result is False

    @pytest.mark.asyncio
    async def test_validate_token_server_error(self, auth_manager, mocker):
        """Test validation with server error response."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = httpx.HTTPError("Server error")

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_client
            result = await auth_manager.validate_token({"Authorization": "Bearer test_token"})
            assert result is False

    @pytest.mark.asyncio
    async def test_update_validation_metadata(self, auth_manager, mock_redis, mock_token_metadata):
        """Test updating validation metadata."""
        mock_redis.get.return_value = json.dumps(mock_token_metadata.to_dict())
        await auth_manager._update_validation_metadata()
        assert mock_redis.setex.called

    @pytest.mark.asyncio
    async def test_invalidate_token_redis_error(self, auth_manager, mock_redis, mock_logger):
        """Test token invalidation with Redis error."""
        mock_redis.delete.side_effect = RedisError("Delete failed")
        await auth_manager.invalidate_token()
        mock_logger.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_token_expiring_soon_ttl(self, auth_manager):
        """Test token expiration check based on TTL."""
        now = time.time()
        metadata = TokenMetadata(
            token="test_token",
            created_at=now,
            expires_at=now + 3000,  # Less than 1 hour remaining
            last_used=now,
            last_validated=now,
            validation_count=0,
        )
        assert await auth_manager._is_token_expiring_soon(metadata) is True

    @pytest.mark.asyncio
    async def test_token_expiring_soon_age(self, auth_manager):
        """Test token expiration check based on age."""
        now = time.time()
        metadata = TokenMetadata(
            token="test_token",
            created_at=now - 50000,  # Older than 12 hours
            expires_at=now + 7200,
            last_used=now,
            last_validated=now,
            validation_count=0,
        )
        assert await auth_manager._is_token_expiring_soon(metadata) is True

    @pytest.mark.asyncio
    async def test_token_expiring_soon_usage(self, auth_manager):
        """Test token expiration check based on usage count."""
        now = time.time()
        metadata = TokenMetadata(
            token="test_token",
            created_at=now,
            expires_at=now + 7200,
            last_used=now,
            last_validated=now,
            validation_count=1001,  # More than 1000 uses
        )
        assert await auth_manager._is_token_expiring_soon(metadata) is True

    @pytest.mark.asyncio
    async def test_acquire_new_token_error_handling(self, auth_manager, mocker):
        """Test error handling during token acquisition."""
        mock_client = AsyncMock()
        mock_client.post.side_effect = httpx.RequestError("Connection failed")

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_client
            with pytest.raises(httpx.RequestError):
                await auth_manager._acquire_new_token()

    @pytest.mark.asyncio
    async def test_get_valid_token_no_metadata(self, auth_manager, mock_redis):
        """Test getting token when no metadata exists."""
        mock_redis.get.return_value = None
        with patch.object(auth_manager, "_acquire_new_token", return_value="new_token"):
            token = await auth_manager.get_valid_token()
            assert token == "new_token"

    @pytest.mark.asyncio
    async def test_update_validation_metadata_no_metadata(self, auth_manager, mock_redis):
        """Test updating validation metadata when no metadata exists."""
        mock_redis.get.return_value = None
        await auth_manager._update_validation_metadata()
        # Should not raise an exception and not call setex
        assert not mock_redis.setex.called

    @pytest.mark.asyncio
    async def test_acquire_new_token_server_error(self, auth_manager, mocker):
        """Test acquiring new token with server error response."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Server error", request=Mock(), response=mock_response
        )

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_client
            with pytest.raises(httpx.HTTPStatusError):
                await auth_manager._acquire_new_token()

    @pytest.mark.asyncio
    async def test_token_expiring_soon_edge_cases(self, auth_manager):
        """Test token expiration edge cases."""
        now = time.time()
        # Test exactly at the thresholds
        metadata = TokenMetadata(
            token="test_token",
            created_at=now - 43200,  # Exactly 12 hours old
            expires_at=now + 3600,  # Exactly 1 hour remaining
            last_used=now,
            last_validated=now,
            validation_count=1000,  # Exactly at max uses
        )
        assert await auth_manager._is_token_expiring_soon(metadata) is True

    @pytest.mark.asyncio
    async def test_store_token_metadata_negative_ttl(self, auth_manager, mock_redis, mock_logger):
        """Test storing token metadata with negative TTL."""
        now = time.time()
        metadata = TokenMetadata(
            token="test_token",
            created_at=now,
            expires_at=now - 1,  # Expired
            last_used=now,
            last_validated=now,
            validation_count=0,
        )
        await auth_manager._store_token_metadata(metadata)
        # Should not attempt to store expired token
        assert not mock_redis.setex.called

    @pytest.mark.asyncio
    async def test_token_expiring_soon_all_conditions_false(self, auth_manager):
        """Test token expiration check when all conditions are false."""
        now = time.time()
        metadata = TokenMetadata(
            token="test_token",
            created_at=now - 3600,  # 1 hour old
            expires_at=now + 7200,  # 2 hours remaining
            last_used=now,
            last_validated=now,
            validation_count=100,
        )
        assert await auth_manager._is_token_expiring_soon(metadata) is False

    @pytest.mark.asyncio
    async def test_update_validation_metadata_redis_error(
        self, auth_manager, mock_redis, mock_token_metadata, mock_logger
    ):
        """Test updating validation metadata with Redis error."""
        mock_redis.get.return_value = json.dumps(mock_token_metadata.to_dict())
        mock_redis.setex.side_effect = RedisError("Storage failed")
        await auth_manager._update_validation_metadata()
        mock_logger.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_acquire_new_token_response_missing_fields(self, auth_manager, mocker):
        """Test acquiring new token with missing fields in response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            # Missing expires_in field
            "access_token": "new_token"
        }

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_client
            with pytest.raises(KeyError):
                await auth_manager._acquire_new_token()

    @pytest.mark.asyncio
    async def test_token_expiring_soon_edge_case_not_expiring(self, auth_manager):
        """Test token expiration edge case where token is not expiring."""
        now = time.time()
        metadata = TokenMetadata(
            token="test_token",
            created_at=now - 43199,  # Just under 12 hours old
            expires_at=now + 3601,  # Just over 1 hour remaining
            last_used=now,
            last_validated=now,
            validation_count=999,  # Just under max uses
        )
        assert await auth_manager._is_token_expiring_soon(metadata) is False
