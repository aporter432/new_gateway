"""Authentication manager for OGx protocol.

This module handles authentication for OGx protocol operations.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional

from httpx import AsyncClient, HTTPStatusError
from redis.asyncio import Redis

from Protexis_Command.core.app_settings import Settings


@dataclass
class TokenMetadata:
    """Token metadata for tracking token state.

    This class encapsulates all metadata related to a token's lifecycle,
    including creation, expiration, usage tracking, and validation history.

    Attributes:
        token: The actual token string
        created_at: Unix timestamp of token creation
        expires_at: Unix timestamp when token expires
        last_used: Unix timestamp of last token usage
        validation_count: Number of successful validations (atomic counter in Redis)
        last_validated: Unix timestamp of last successful validation
    """

    token: str
    created_at: float
    expires_at: float
    last_used: float
    validation_count: int = 0
    last_validated: Optional[float] = None


class OGxAuthManager:
    """Manages OGx authentication and token lifecycle.

    This class provides thread-safe token management with Redis-based storage.
    It handles token acquisition, validation, refresh, and metadata tracking
    with support for concurrent access patterns.

    Implementation Details:
    - Uses Redis atomic operations for thread-safe updates
    - Maintains token metadata in Redis hash structures
    - Handles token expiration and automatic refresh
    - Provides atomic validation counting for concurrent access

    Redis Key Structure:
    - {prefix}:auth:token - Token storage
    - {prefix}:auth:token:metadata - Token metadata storage
    """

    def __init__(self, settings: Settings, redis: Redis):
        """Initialize auth manager.

        Args:
            settings: Application settings containing OGx credentials and configuration
            redis: Redis client for token and metadata storage
        """
        self.settings = settings
        self.redis = redis
        self._token_key = "OGx:auth:token"
        self._metadata_key = "OGx:auth:token:metadata"

    async def get_valid_token(
        self, force_refresh: bool = False, expires_in: Optional[int] = None
    ) -> str:
        """Get a valid authentication token.

        Args:
            force_refresh: Force token refresh even if current token is valid
            expires_in: Optional token expiry time in seconds

        Returns:
            Valid authentication token

        Raises:
            HTTPError: If authentication fails
        """
        # Check for existing valid token
        if not force_refresh:
            metadata = await self._get_token_metadata()
            if metadata:
                now = datetime.now().timestamp()
                # Check if token is expired
                if metadata.expires_at > now:
                    # Update last used time
                    metadata.last_used = now
                    await self._store_token_metadata(metadata)
                    return metadata.token

        # Make token request
        async with AsyncClient() as client:
            response = await client.post(
                f"{self.settings.OGx_BASE_URL}/auth/token",
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.settings.OGx_CLIENT_ID,
                    "client_secret": self.settings.OGx_CLIENT_SECRET,
                    "expires_in": expires_in,
                },
            )

            # Handle response
            response.raise_for_status()
            data = response.json()
            token = data["access_token"]  # Use token from response
            token_expires_in = data.get("expires_in", 604800)  # Default to 7 days

            # Store token metadata
            now = datetime.now().timestamp()
            metadata = TokenMetadata(
                token=token,
                created_at=now,
                expires_at=now + token_expires_in,
                last_used=now,
                validation_count=0,
                last_validated=None,
            )
            await self._store_token_metadata(metadata)
            return token

    async def validate_token(self, auth_header: Dict[str, str]) -> bool:
        """Validate authentication token with atomic metadata updates.

        This method validates a token against the OGx API and updates token metadata
        atomically in Redis. It handles concurrent validation requests safely using
        Redis atomic operations.

        Implementation Details:
        - Uses Redis HINCRBY for atomic validation counting
        - Uses Redis pipeline for atomic metadata updates
        - Handles token expiration and invalidation
        - Updates usage and validation timestamps

        Args:
            auth_header: Authorization header containing token

        Returns:
            True if token is valid and metadata was updated successfully

        Thread Safety:
        This method is thread-safe and handles concurrent validation requests
        correctly through Redis atomic operations.
        """
        token = auth_header.get("Authorization", "").replace("Bearer ", "")
        if not token:
            return False

        try:
            # Make validation request to OGx API
            async with AsyncClient() as client:
                response = await client.get(
                    f"{self.settings.OGx_BASE_URL}/auth/validate",
                    headers=auth_header,
                )
                response.raise_for_status()

            # Get current metadata first
            metadata = await self._get_token_metadata()
            if not metadata or metadata.token != token:
                return False

            now = datetime.now().timestamp()
            if metadata.expires_at <= now:
                await self.invalidate_token()
                return False

            # Update metadata atomically
            try:
                async with self.redis.pipeline() as pipe:
                    # Use atomic operations for updates
                    await pipe.hincrby(
                        self._metadata_key, "validation_count", 1
                    )  # Atomic increment
                    await pipe.hset(
                        self._metadata_key,
                        mapping={
                            "token": metadata.token,
                            "created_at": str(metadata.created_at),
                            "expires_at": str(metadata.expires_at),
                            "last_used": str(now),
                            "last_validated": str(now),
                        },
                    )
                    await pipe.execute()
                return True
            except Exception:
                return False

        except HTTPStatusError as e:
            if e.response.status_code in (401, 403):
                await self.invalidate_token()
            return False
        except Exception:
            return False

    async def get_token_info(self) -> Optional[Dict[str, Any]]:
        """Get current token information.

        Returns:
            Token metadata if available
        """
        metadata = await self._get_token_metadata()
        if not metadata:
            return None

        return {
            "token": metadata.token[-8:],  # Last 8 chars for security
            "created_at": metadata.created_at,
            "expires_at": metadata.expires_at,
            "last_used": metadata.last_used,
            "validation_count": metadata.validation_count,
            "last_validated": metadata.last_validated,
        }

    async def get_auth_header(self) -> Dict[str, str]:
        """Get authorization header with valid token.

        Returns:
            Dict containing Authorization header with Bearer token
        """
        token = await self.get_valid_token()
        return {"Authorization": f"Bearer {token}"}

    async def invalidate_token(self) -> None:
        """Invalidate current token."""
        await self.redis.delete(self._token_key)
        await self.redis.delete(self._metadata_key)

    async def _store_token_metadata(self, metadata: TokenMetadata) -> None:
        """Store token metadata in Redis.

        This method stores token metadata in a Redis hash structure. All fields
        are stored as strings to maintain compatibility with Redis hash requirements.

        Args:
            metadata: Token metadata to store
        """
        await self.redis.hset(
            self._metadata_key,
            mapping={
                "token": metadata.token,
                "created_at": str(metadata.created_at),
                "expires_at": str(metadata.expires_at),
                "last_used": str(metadata.last_used),
                "validation_count": str(metadata.validation_count),
                "last_validated": str(metadata.last_validated) if metadata.last_validated else "",
            },
        )

    async def _get_token_metadata(self) -> Optional[TokenMetadata]:
        """Get token metadata from Redis.

        This method retrieves and deserializes token metadata from Redis.
        It handles type conversion and optional fields appropriately.

        Returns:
            TokenMetadata if available and valid, None otherwise

        Note:
            This method is not atomic with respect to other operations.
            For atomic updates, use Redis transactions or atomic operations.
        """
        data = await self.redis.hgetall(self._metadata_key)
        if not data:
            return None

        try:
            # Convert Redis response to string keys
            str_data = {
                k.decode() if isinstance(k, bytes) else k: v.decode() if isinstance(v, bytes) else v
                for k, v in data.items()
            }

            return TokenMetadata(
                token=str_data["token"],
                created_at=float(str_data["created_at"]),
                expires_at=float(str_data["expires_at"]),
                last_used=float(str_data["last_used"]),
                validation_count=int(str_data["validation_count"]),
                last_validated=float(str_data["last_validated"])
                if str_data.get("last_validated")
                else None,
            )
        except (KeyError, ValueError, TypeError) as e:
            self.logger.error(f"Failed to parse token metadata: {str(e)}")
            return None
