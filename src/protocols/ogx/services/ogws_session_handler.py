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
from typing import Dict, Optional, cast
import uuid

from redis.asyncio import Redis

from core.app_settings import get_settings
from core.logging.loggers import get_protocol_logger
from core.security import OGWSAuthManager
from infrastructure.redis import get_redis_client
from protocols.ogx.constants.error_codes import HTTPErrorCode
from protocols.ogx.validation.common.validation_exceptions import (
    AuthenticationError,
    OGxProtocolError,
    RateLimitError,
    ValidationError,
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
        max_concurrent_sessions_per_customer: Maximum allowed concurrent sessions per customer
        session_timeout: Session timeout in seconds
    """

    def __init__(self) -> None:
        """Initialize session handler."""
        self.settings = get_settings()
        self.logger = get_protocol_logger("session_handler")
        self.auth_manager: Optional[OGWSAuthManager] = None
        self.redis: Optional[Redis] = None
        self.session_key_prefix = "ogws:session:"
        self.max_concurrent_sessions_per_customer = 3  # Per customer limit
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
        self.redis = cast(Redis, redis)  # Cast to help type checker

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
            RuntimeError: If handler not initialized
            AuthenticationError: If authentication fails
            RateLimitError: If session limit exceeded
            ValidationError: If required credentials are missing
            OGxProtocolError: For other session errors
        """
        if not self.auth_manager or not self.redis:
            raise RuntimeError("SessionHandler not initialized")

        try:
            # Get customer ID from credentials
            customer_id = credentials.get("client_id")
            if not customer_id:
                self.logger.error(
                    "Missing client_id in credentials",
                    extra={
                        "customer_id": "unknown",
                        "asset_id": "session_handler",
                        "action": "create_session",
                    },
                )
                raise ValidationError("client_id is required")

            # Check concurrent session limit for this customer
            active_sessions = await self._get_customer_session_count(customer_id)
            if active_sessions >= self.max_concurrent_sessions_per_customer:
                raise RateLimitError(
                    f"Maximum concurrent sessions ({self.max_concurrent_sessions_per_customer}) exceeded for customer {customer_id}",
                    error_code=HTTPErrorCode.TOO_MANY_REQUESTS,
                )

            # Get auth token
            token = await self.auth_manager.get_valid_token()

            # Create session
            session_id = await self._create_session_record(token, customer_id)

            self.logger.info(
                "Session created",
                extra={
                    "customer_id": customer_id,
                    "asset_id": "session_handler",
                    "session_id": session_id,
                    "action": "create_session",
                },
            )

            return session_id

        except (AuthenticationError, RateLimitError, ValidationError, OGxProtocolError) as e:
            self.logger.error(
                "Session creation failed",
                extra={
                    "customer_id": credentials.get("client_id", "unknown"),
                    "asset_id": "session_handler",
                    "error": str(e),
                    "action": "create_session",
                },
            )
            raise

        except Exception as e:
            self.logger.error(
                "Unexpected error during session creation",
                extra={
                    "customer_id": credentials.get("client_id", "unknown"),
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

        Raises:
            RuntimeError: If handler not initialized
        """
        if not self.auth_manager or not self.redis:
            raise RuntimeError("SessionHandler not initialized")

        try:
            # Get session data
            session_key = f"{self.session_key_prefix}{session_id}"
            try:
                session_data = await self.redis.hgetall(session_key)
            except Exception:
                # Silently fail for Redis errors during initial retrieval
                return False

            if not session_data:
                return False

            # Extract token and validate
            token = session_data.get(b"token", b"").decode()
            if not token:
                return False

            # Update last activity timestamp before validation
            try:
                await self.redis.hset(
                    session_key,
                    "last_activity",
                    datetime.now().isoformat(),
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
                # Return False if we can't update last activity
                return False

            # Validate token with auth manager
            try:
                auth_header = {"Authorization": f"Bearer {token}"}
                await self.auth_manager.validate_token(auth_header)
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

            return True

        except Exception as e:
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
        """End an active session.

        Args:
            session_id: Session ID to end

        Raises:
            RuntimeError: If handler not initialized
            OGxProtocolError: If session cannot be ended
        """
        if not self.auth_manager or not self.redis:
            raise RuntimeError("SessionHandler not initialized")

        try:
            # Get session data to find customer ID
            session_key = f"{self.session_key_prefix}{session_id}"
            session_data = await self.redis.hgetall(session_key)
            customer_id = session_data.get(b"customer_id", b"").decode()

            # Delete session
            await self.redis.delete(session_key)

            # Remove from customer's session set if customer ID exists
            if customer_id:
                customer_sessions_key = f"{self.session_key_prefix}customer:{customer_id}"
                await self.redis.srem(customer_sessions_key, session_id)

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
            error_msg = f"Failed to end session: {str(e)}"
            self.logger.error(
                error_msg,
                extra={
                    "customer_id": self.settings.CUSTOMER_ID,
                    "asset_id": "session_handler",
                    "session_id": session_id,
                    "error": str(e),
                    "action": "end_session",
                },
            )
            raise OGxProtocolError(error_msg) from e

    async def refresh_session(self, session_id: str) -> None:
        """Refresh session token.

        Args:
            session_id: Session ID to refresh

        Raises:
            RuntimeError: If handler not initialized
            OGxProtocolError: If session cannot be refreshed
        """
        if not self.auth_manager or not self.redis:
            raise RuntimeError("SessionHandler not initialized")

        try:
            # Get new token
            token = await self.auth_manager.get_valid_token()

            # Update session data
            session_key = f"{self.session_key_prefix}{session_id}"
            await self.redis.hset(session_key, "token", token)
            await self.redis.hset(
                session_key,
                "last_activity",
                datetime.now().isoformat(),
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
            error_msg = f"Failed to refresh session: {str(e)}"
            self.logger.error(
                error_msg,
                extra={
                    "customer_id": self.settings.CUSTOMER_ID,
                    "asset_id": "session_handler",
                    "session_id": session_id,
                    "error": str(e),
                    "action": "refresh_session",
                },
            )
            raise OGxProtocolError(error_msg) from e

    async def _create_session_record(self, token: str, customer_id: str) -> str:
        """Create session record in Redis.

        Args:
            token: Authentication token for session
            customer_id: Customer ID for the session

        Returns:
            New session ID

        Raises:
            OGxProtocolError: If session record cannot be created
        """
        session_id = str(uuid.uuid4())
        session_key = f"{self.session_key_prefix}{session_id}"
        now = datetime.now().isoformat()

        session_data = {
            b"token": token.encode(),
            b"created_at": now.encode(),
            b"last_activity": now.encode(),
            b"request_count": b"0",
            b"customer_id": customer_id.encode(),
        }

        try:
            if self.redis:  # Type checker hint
                for key, value in session_data.items():
                    await self.redis.hset(session_key, key, value)
                await self.redis.expire(session_key, self.session_timeout)

                # Add to customer's session set
                customer_sessions_key = f"{self.session_key_prefix}customer:{customer_id}"
                await self.redis.sadd(customer_sessions_key, session_id)
                await self.redis.expire(customer_sessions_key, self.session_timeout)

            return session_id
        except Exception as e:
            raise OGxProtocolError(f"Failed to create session record: {str(e)}") from e

    async def _get_customer_session_count(self, customer_id: str) -> int:
        """Get count of active sessions for a specific customer.

        Args:
            customer_id: Customer ID to check sessions for

        Returns:
            Number of active sessions for the customer

        Raises:
            OGxProtocolError: If session count cannot be retrieved
        """
        try:
            if self.redis:
                customer_sessions_key = f"{self.session_key_prefix}customer:{customer_id}"
                return await self.redis.scard(customer_sessions_key)
            return 0
        except Exception as e:
            raise OGxProtocolError(f"Failed to get customer session count: {str(e)}") from e
