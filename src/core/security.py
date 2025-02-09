"""Token management and authentication for OGWS integration.

This module handles:
- Token acquisition and storage
- Token validation and refresh
- Authentication header management
- Token lifecycle and metadata management
"""

import json
import time
from typing import Dict, Optional

import httpx
from httpx import HTTPError
from redis.asyncio import Redis
from redis.exceptions import RedisError

from core.app_settings import Settings, get_settings
from core.exceptions import OGxProtocolError
from core.logging.loggers import get_auth_logger
from infrastructure.redis import get_redis_client


class TokenMetadata:
    """Token metadata container."""

    def __init__(
        self,
        token: str,
        created_at: float,
        expires_at: float,
        last_used: float,
        last_validated: Optional[float] = None,
        validation_count: int = 0,
    ):
        self.token = token
        self.created_at = created_at
        self.expires_at = expires_at
        self.last_used = last_used
        self.last_validated = last_validated
        self.validation_count = validation_count

    def to_dict(self) -> dict:
        """Convert metadata to dictionary for storage."""
        return {
            "token": self.token,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "last_used": self.last_used,
            "last_validated": self.last_validated,
            "validation_count": self.validation_count,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TokenMetadata":
        """Create metadata instance from dictionary."""
        return cls(
            token=data["token"],
            created_at=data["created_at"],
            expires_at=data["expires_at"],
            last_used=data["last_used"],
            last_validated=data["last_validated"],
            validation_count=data["validation_count"],
        )


class OGWSAuthManager:
    """Manages OGWS authentication and token lifecycle."""

    def __init__(self, settings: Settings, redis: Redis):
        self.settings = settings
        self.redis = redis
        self.token_key = "ogws:auth:token"
        self.token_metadata_key = "ogws:auth:token:metadata"
        self.logger = get_auth_logger("auth_manager")

    async def get_valid_token(self, force_refresh: bool = False) -> str:
        """Get a valid token, refreshing if necessary or if forced.

        Args:
            force_refresh: If True, always get a new token regardless of current state
        """
        if not force_refresh:
            metadata = await self._get_token_metadata()
            if metadata and not await self._is_token_expiring_soon(metadata):
                await self._update_last_used(metadata)
                return metadata.token

        return await self._acquire_new_token()

    async def get_auth_header(self) -> dict:
        """Get authorization header with valid token.

        Implementation follows OGWS-1.txt Section 4.1.1:
        - Bearer token authentication
        - Automatic token refresh
        - Token expiration handling
        - Proper header formatting

        Returns:
            Dict containing Authorization header with Bearer token

        Raises:
            OGxProtocolError: If unable to get valid token
        """
        try:
            token = await self.get_valid_token()
            return {"Authorization": f"Bearer {token}"}
        except Exception as e:
            raise OGxProtocolError(f"Failed to get authorization header: {str(e)}") from e

    async def validate_token(self, auth_header: dict) -> bool:
        """Validate token by calling the info/service endpoint."""
        try:
            transport = httpx.AsyncHTTPTransport(local_address="0.0.0.0")
            async with httpx.AsyncClient(transport=transport, verify=False) as client:
                response = await client.get(
                    f"{self.settings.OGWS_BASE_URL}/info/service",
                    headers=auth_header,
                )
                # If we get a 401, the token is invalid
                if response.status_code == 401:
                    return False

                # Any other error status code indicates a server/network issue
                if response.status_code >= 400:
                    response.raise_for_status()

                # If we get here, the token is valid
                # Update validation metadata
                await self._update_validation_metadata()
                return True

        except (HTTPError, ValueError) as e:
            self.logger.warning(
                "Token validation failed with service info endpoint",
                extra={
                    "customer_id": self.settings.CUSTOMER_ID,
                    "asset_id": "auth_service",
                    "auth_info": {
                        "error_type": "validation",
                        "error_msg": str(e),
                        "service": "OGWS",
                        "endpoint": "info/service",
                    },
                },
            )
            return False

    async def invalidate_token(self) -> None:
        """Invalidate and remove current token."""
        try:
            await self.redis.delete(self.token_metadata_key)
            await self.redis.delete(self.token_key)
        except RedisError as e:
            self.logger.error(
                "Failed to invalidate token",
                extra={
                    "customer_id": self.settings.CUSTOMER_ID,
                    "asset_id": "auth_service",
                    "auth_info": {
                        "error_type": "storage",
                        "error_msg": str(e),
                        "service": "OGWS",
                    },
                },
            )

    async def get_token_info(self) -> Optional[Dict]:
        """Get current token metadata as dictionary."""
        metadata = await self._get_token_metadata()
        if metadata:
            return {
                "token": metadata.token[-8:],  # Last 8 chars for security
                "created_at": metadata.created_at,
                "expires_at": metadata.expires_at,
                "last_used": metadata.last_used,
                "last_validated": metadata.last_validated,
                "validation_count": metadata.validation_count,
                "ttl": metadata.expires_at - time.time(),
            }
        return None

    # Private methods for token management
    async def _get_token_metadata(self) -> Optional[TokenMetadata]:
        """Retrieve token metadata if available."""
        try:
            data = await self.redis.get(self.token_metadata_key)
            if data:
                return TokenMetadata.from_dict(json.loads(data))
            return None
        except (RedisError, json.JSONDecodeError):
            return None

    async def _store_token_metadata(self, metadata: TokenMetadata) -> None:
        """Store token metadata in Redis."""
        try:
            ttl = int(metadata.expires_at - time.time())
            if ttl > 0:
                await self.redis.setex(self.token_metadata_key, ttl, json.dumps(metadata.to_dict()))
                await self.redis.setex(self.token_key, ttl, metadata.token)
        except RedisError as e:
            self.logger.error(
                "Failed to store token metadata",
                extra={
                    "customer_id": self.settings.CUSTOMER_ID,
                    "asset_id": "auth_service",
                    "auth_info": {
                        "error_type": "storage",
                        "error_msg": str(e),
                        "service": "OGWS",
                    },
                },
            )

    async def _update_last_used(self, metadata: TokenMetadata) -> None:
        """Update token's last used timestamp."""
        metadata.last_used = time.time()
        await self._store_token_metadata(metadata)

    async def _update_validation_metadata(self) -> None:
        """Update token's validation metadata."""
        metadata = await self._get_token_metadata()
        if metadata:
            metadata.last_validated = time.time()
            metadata.validation_count += 1
            await self._store_token_metadata(metadata)

    async def _is_token_expiring_soon(self, metadata: TokenMetadata) -> bool:
        """Check if token needs refresh based on expiry time.

        Refreshes token if:
        - Less than 1 hour remaining
        - Token is older than max age
        - Token has been used more than max uses
        """
        now = time.time()
        ttl = metadata.expires_at - now

        # Refresh if less than 1 hour remaining
        if ttl < 3600:
            return True

        # Refresh if token is older than 12 hours
        if now - metadata.created_at > 43200:
            return True

        # Refresh if token has been used more than 1000 times
        if metadata.validation_count > 1000:
            return True

        return False

    async def _acquire_new_token(self) -> str:
        """Acquire new token from OGWS using client credentials flow."""
        url = f"{self.settings.OGWS_BASE_URL}/auth/token"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = f"client_id={self.settings.OGWS_CLIENT_ID}&client_secret={self.settings.OGWS_CLIENT_SECRET}&grant_type=client_credentials"

        # Don't use proxy for localhost
        transport = httpx.AsyncHTTPTransport(local_address="0.0.0.0")
        async with httpx.AsyncClient(transport=transport, verify=False) as client:
            response = await client.post(
                url,
                headers=headers,
                content=data,
            )
            if response.status_code >= 400:
                response.raise_for_status()
            token_data = response.json()

            # Store metadata
            now = time.time()
            metadata = TokenMetadata(
                token=token_data["access_token"],
                created_at=now,
                expires_at=now + token_data["expires_in"],
                last_used=now,
            )
            await self._store_token_metadata(metadata)
            return metadata.token


async def get_auth_manager() -> OGWSAuthManager:
    """Get configured auth manager instance."""
    settings = get_settings()
    redis = await get_redis_client()
    return OGWSAuthManager(settings=settings, redis=redis)
