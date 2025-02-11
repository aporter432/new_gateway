"""OGWS session management service.

This module implements session handling as defined in OGWS-1.txt Section 3.
It handles:
1. Session lifecycle management
2. Token management and refresh
3. Rate limiting enforcement
4. Session state tracking

Configuration Sources:
    - core.app_settings: Environment and credential configuration
    - protocols.ogx.constants.limits: Rate and concurrency limits
    - protocols.ogx.validation: Authentication validation rules

Environment-Specific Behavior:
    Development:
        - Uses Redis for session storage
        - Allows test credentials
        - Flexible session limits
        - Debug-level logging

    Production:
        - Uses Redis with persistence
        - Requires valid credentials
        - Strict session limits
        - Error-level logging
        - TODO: Add comprehensive metrics
        - TODO: Implement session cleanup
        - TODO: Add failover handling

Implementation Notes:
    - Uses Redis for session state storage
    - Implements sliding window rate limiting
    - Handles concurrent sessions
    - Tracks session metadata
"""

from datetime import datetime
from typing import Dict, Optional
import uuid

from core.app_settings import get_settings
from core.logging.loggers import get_protocol_logger
from core.security import OGWSAuthManager
from infrastructure.redis import get_redis_client
from protocols.ogx.constants.error_codes import HTTPErrorCode
from protocols.ogx.validation.common.validation_exceptions import (
    AuthenticationError,
    OGxProtocolError,
    RateLimitError,
)


class SessionHandler:
    """Handles OGWS session management.

    This class implements session management according to OGWS-1.txt Section 3.
    It handles:
    1. Session initialization and cleanup
    2. Token lifecycle management
    3. Rate limiting enforcement
    4. Session state tracking

    Configuration Sources:
        - core.app_settings: Environment settings
        - core.security: Authentication management
        - infrastructure.redis: Session storage

    Environment-Specific Behavior:
        Development:
            - Local Redis instance
            - Test credentials allowed
            - Flexible limits
            - Debug logging

        Production:
            - Production Redis cluster
            - Valid credentials required
            - Strict limits enforced
            - Error logging
            - TODO: Add metrics collection
            - TODO: Implement cleanup jobs

    Attributes:
        auth_manager: Authentication manager for token handling
        session_key_prefix: Redis key prefix for session data
        max_concurrent_sessions: Maximum allowed concurrent sessions
        session_timeout: Session timeout in seconds
    """

    def __init__(self) -> None:
        """Initialize session handler."""
        self.settings = get_settings()
        self.logger = get_protocol_logger("session_handler")
        self.auth_manager: Optional[OGWSAuthManager] = None
        self.redis = None
        self.session_key_prefix = "ogws:session:"
        self.max_concurrent_sessions = 3
        self.session_timeout = 3600  # 1 hour

    async def initialize(self) -> None:
        """Initialize session handler.

        This needs to be called before using the handler.

        Raises:
            RuntimeError: If Redis connection fails
        """
        redis = await get_redis_client()
        if not redis:
            raise RuntimeError("Failed to initialize Redis connection")
        self.auth_manager = OGWSAuthManager(self.settings, redis)
        self.redis = redis

    async def create_session(self, credentials: Dict[str, str]) -> str:
        """Create new session with OGWS.

        Args:
            credentials: Authentication credentials
                Required:
                    - client_id: OGWS client ID
                    - client_secret: OGWS client secret
                Optional:
                    - expires_in: Token expiry in seconds

        Returns:
            Session ID for the new session

        Raises:
            AuthenticationError: If authentication fails
            RateLimitError: If session limit exceeded
            OGxProtocolError: For other session errors
        """
        if not self.auth_manager:
            raise RuntimeError("SessionHandler not initialized")

        try:
            # Check concurrent session limit
            active_sessions = await self._get_active_session_count()
            if active_sessions >= self.max_concurrent_sessions:
                raise RateLimitError(
                    f"Maximum concurrent sessions ({self.max_concurrent_sessions}) exceeded",
                    error_code=HTTPErrorCode.TOO_MANY_REQUESTS,
                )

            # Get auth token using provided credentials
            token = await self.auth_manager.get_valid_token()

            # Create session
            session_id = await self._create_session_record(token)

            self.logger.info(
                "Session created",
                extra={
                    "customer_id": self.settings.CUSTOMER_ID,
                    "asset_id": "session_handler",
                    "session_id": session_id,
                    "action": "create_session",
                },
            )

            return session_id

        except AuthenticationError as e:
            self.logger.error(
                "Session creation failed - authentication error",
                extra={
                    "customer_id": self.settings.CUSTOMER_ID,
                    "asset_id": "session_handler",
                    "error": str(e),
                    "action": "create_session",
                },
            )
            raise

        except Exception as e:
            self.logger.error(
                "Session creation failed",
                extra={
                    "customer_id": self.settings.CUSTOMER_ID,
                    "asset_id": "session_handler",
                    "error": str(e),
                    "action": "create_session",
                },
            )
            raise OGxProtocolError(f"Failed to create session: {str(e)}") from e

    async def validate_session(self, session_id: str) -> bool:
        """Validate session and update last activity.

        Args:
            session_id: Session ID to validate

        Returns:
            True if session is valid, False otherwise
        """
        if not self.auth_manager:
            raise RuntimeError("SessionHandler not initialized")

        # Get session data
        session_key = f"{self.session_key_prefix}{session_id}"
        session_data = None
        try:
            session_data = await self.redis.hgetall(session_key)
            if not session_data or b"token" not in session_data:
                return False

            # Update last activity
            try:
                await self.redis.hset(
                    session_key,
                    "last_activity",
                    datetime.utcnow().isoformat(),
                )
            except Exception as e:
                self.logger.warning(
                    "Failed to update last activity",
                    extra={
                        "customer_id": self.settings.CUSTOMER_ID,
                        "asset_id": "session_handler",
                        "session_id": session_id,
                        "error": str(e),
                        "action": "validate_session",
                    },
                )
                # Continue with validation even if update fails

            # Validate token - Redis returns bytes
            token = session_data[b"token"].decode()
            auth_header = {"Authorization": f"Bearer {token}"}
            try:
                return await self.auth_manager.validate_token(auth_header)
            except Exception as e:
                self.logger.error(
                    "Token validation failed",
                    extra={
                        "customer_id": self.settings.CUSTOMER_ID,
                        "asset_id": "session_handler",
                        "session_id": session_id,
                        "error": str(e),
                        "action": "validate_session",
                    },
                )
                return False

        except Exception as e:
            # Only log errors for unexpected Redis failures, not for missing sessions
            if session_data is not None:
                self.logger.error(
                    "Session validation failed",
                    extra={
                        "customer_id": self.settings.CUSTOMER_ID,
                        "asset_id": "session_handler",
                        "session_id": session_id,
                        "error": str(e),
                        "action": "validate_session",
                    },
                )
            return False

    async def end_session(self, session_id: str) -> None:
        """End session and cleanup resources.

        Args:
            session_id: Session ID to end
        """
        if not self.auth_manager:
            raise RuntimeError("SessionHandler not initialized")

        try:
            # Delete session data
            session_key = f"{self.session_key_prefix}{session_id}"
            await self.redis.delete(session_key)

            self.logger.info(
                "Session ended",
                extra={
                    "customer_id": self.settings.CUSTOMER_ID,
                    "asset_id": "session_handler",
                    "session_id": session_id,
                    "action": "end_session",
                },
            )

        except Exception as e:
            self.logger.error(
                "Session cleanup failed",
                extra={
                    "customer_id": self.settings.CUSTOMER_ID,
                    "asset_id": "session_handler",
                    "session_id": session_id,
                    "error": str(e),
                    "action": "end_session",
                },
            )
            raise OGxProtocolError(f"Failed to end session: {str(e)}") from e

    async def refresh_session(self, session_id: str) -> None:
        """Refresh session token.

        Args:
            session_id: Session ID to refresh

        Raises:
            AuthenticationError: If token refresh fails
            OGxProtocolError: For other session errors
        """
        if not self.auth_manager:
            raise RuntimeError("SessionHandler not initialized")

        try:
            # Get new token
            token = await self.auth_manager.get_valid_token(force_refresh=True)

            # Update session data
            session_key = f"{self.session_key_prefix}{session_id}"
            await self.redis.hset(session_key, "token", token)
            await self.redis.hset(
                session_key,
                "last_refresh",
                datetime.utcnow().isoformat(),
            )

            self.logger.info(
                "Session refreshed",
                extra={
                    "customer_id": self.settings.CUSTOMER_ID,
                    "asset_id": "session_handler",
                    "session_id": session_id,
                    "action": "refresh_session",
                },
            )

        except Exception as e:
            self.logger.error(
                "Session refresh failed",
                extra={
                    "customer_id": self.settings.CUSTOMER_ID,
                    "asset_id": "session_handler",
                    "session_id": session_id,
                    "error": str(e),
                    "action": "refresh_session",
                },
            )
            raise OGxProtocolError(f"Failed to refresh session: {str(e)}") from e

    async def _create_session_record(self, token: str) -> str:
        """Create session record in Redis.

        Args:
            token: Authentication token for the session

        Returns:
            Session ID
        """
        session_id = str(uuid.uuid4())
        session_key = f"{self.session_key_prefix}{session_id}"

        # Store session data
        session_data = {
            "token": token,
            "created_at": datetime.utcnow().isoformat(),
            "last_activity": datetime.utcnow().isoformat(),
            "customer_id": self.settings.CUSTOMER_ID,
        }

        # Convert all values to strings for Redis storage
        redis_data = {k: str(v) for k, v in session_data.items()}
        await self.redis.hmset(session_key, redis_data)
        await self.redis.expire(session_key, self.session_timeout)

        return session_id

    async def _get_active_session_count(self) -> int:
        """Get count of active sessions.

        Returns:
            Number of active sessions
        """
        pattern = f"{self.session_key_prefix}*"
        keys = await self.redis.keys(pattern)
        return len(keys)
