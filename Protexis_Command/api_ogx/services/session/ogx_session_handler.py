"""OGx Gateway Web Service (OGx) Session Handler.

This module implements session management for OGx according to OGx-1.txt Section 3.1.
It handles:
1. Session creation and validation
2. Token management and refresh
3. Concurrent session limits
4. Session cleanup and expiry
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Set, Type, cast

from redis.asyncio import Redis
from redis.exceptions import RedisError

from Protexis_Command.core.logging.loggers import get_protocol_logger
from Protexis_Command.infrastructure.cache.redis import get_redis_client
from Protexis_Command.protocol.ogx.ogx_protocol_handler import OGxProtocolHandler
from Protexis_Command.protocol.ogx.validation.ogx_validation_exceptions import (
    AuthenticationError,
    OGxProtocolError,
    ValidationError,
)

# Get logger - protocol logger includes metrics capabilities
logger = get_protocol_logger()

# Constants
MAX_CONCURRENT_SESSIONS = 5  # Maximum concurrent sessions per client
SESSION_TIMEOUT = 3600  # Default session timeout in seconds (1 hour)
TOKEN_REFRESH_WINDOW = 60 * 60  # 1 hour refresh window
CLEANUP_INTERVAL = 300  # Interval in seconds between cleanup runs (5 minutes)

# Metric names
METRIC_SESSION_CREATED = "ogx.session.created"
METRIC_SESSION_VALIDATED = "ogx.session.validated"
METRIC_SESSION_REFRESHED = "ogx.session.refreshed"
METRIC_SESSION_ENDED = "ogx.session.ended"
METRIC_SESSION_EXPIRED = "ogx.session.expired"
METRIC_ACTIVE_SESSIONS = "ogx.session.active"
METRIC_AUTH_FAILURES = "ogx.session.auth_failures"
METRIC_SESSION_COUNT = "ogx.session.count"
METRIC_SESSION_RENEWED = "ogx.session.renewed"

# Type aliases
RedisData = Dict[str, str]
# No need for explicit RedisMapping type alias - we'll cast at call site


# Define a helper function to format timestamps according to OGx specification
def format_ogx_timestamp(dt: datetime) -> str:
    """Format a datetime object according to OGx specification (YYYY-MM-DD hh:mm:ss)."""
    return dt.strftime("%Y-%m-%d %H:%M:%S")


# Define a helper function to parse OGx formatted timestamps
def parse_ogx_timestamp(timestamp_str: str) -> datetime:
    """Parse a timestamp string in OGx format (YYYY-MM-DD hh:mm:ss) to a datetime object."""
    return datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")


class SessionHandler:
    """Handles OGx session management using Redis.

    This class implements the session management requirements from OGx-1.txt Section 3.1,
    including session creation, validation, refresh, and cleanup.

    Attributes:
        redis: Redis client for session storage
        _cleanup_task: Background task for session cleanup
        _protocol_handler: OGx protocol handler for authentication
    """

    def __init__(self, protocol_handler_cls: Type[OGxProtocolHandler]) -> None:
        """Initialize session handler.

        Args:
            protocol_handler_cls: OGx protocol handler class to use for authentication
        """
        self.redis: Optional[Redis] = None
        self._cleanup_task: Optional[asyncio.Task] = None
        self._protocol_handler: Optional[OGxProtocolHandler] = None
        self._protocol_handler_cls = protocol_handler_cls
        logger.debug(
            "Initialized SessionHandler with protocol handler %s",
            protocol_handler_cls.__name__,
        )

    async def initialize(self) -> None:
        """Initialize Redis connection and start cleanup task."""
        if self.redis is not None:
            return

        logger.info("Initializing SessionHandler")

        try:
            # Initialize Redis connection using infrastructure client
            self.redis = await get_redis_client()
            logger.debug("Redis connection initialized")

            # Initialize protocol handler
            self._protocol_handler = self._protocol_handler_cls()
            logger.debug("Protocol handler initialized")

            # Start cleanup task
            if self._cleanup_task is None:
                self._cleanup_task = asyncio.create_task(self._cleanup_loop())
                logger.debug("Cleanup task started")

        except (RedisError, IOError, RuntimeError) as e:
            logger.error("Failed to initialize SessionHandler: %s", str(e))
            raise OGxProtocolError(f"Failed to initialize session handler: {str(e)}") from e

    async def create_session(self, credentials: Dict[str, Any]) -> str:
        """Create a new session with the given credentials.

        Args:
            credentials: Authentication credentials (client_id, client_secret, etc.)

        Returns:
            str: A unique session ID for the newly created session

        Raises:
            ValidationError: If credentials are invalid
            AuthenticationError: If authentication fails
            OGxProtocolError: If session creation fails
        """
        logger.debug("Creating new session")

        if not credentials or "client_id" not in credentials or "client_secret" not in credentials:
            logger.warning("Missing required credentials")
            raise ValidationError("Missing required credentials")

        client_id = credentials["client_id"]
        client_secret = credentials["client_secret"]
        expires_in = credentials.get("expires_in", SESSION_TIMEOUT)

        # Check if redis is initialized
        if not self.redis:
            logger.error("Attempted to create session before initialization")
            raise OGxProtocolError("Session handler not initialized")

        # Check concurrent session limit
        try:
            client_sessions_key = f"client_sessions:{client_id}"
            session_count = await self.redis.scard(client_sessions_key)
            if session_count >= MAX_CONCURRENT_SESSIONS:
                logger.warning(
                    "Maximum concurrent sessions exceeded for client %s: %d",
                    client_id,
                    session_count,
                )
                raise OGxProtocolError("Maximum concurrent sessions exceeded")
        except RedisError as e:
            logger.error("Failed to check session count: %s", str(e))
            raise OGxProtocolError(f"Failed to check session count: {str(e)}") from e

        try:
            # Authenticate with OGx protocol handler
            if not self._protocol_handler:
                logger.error("Protocol handler not initialized")
                raise OGxProtocolError("Protocol handler not initialized")

            # Create a credentials dict for the authenticate method
            auth_credentials = {"client_id": client_id, "client_secret": client_secret}
            token = await self._protocol_handler.authenticate(auth_credentials)
            if not token:
                logger.warning("Authentication failed for client %s", client_id)
                raise AuthenticationError("Authentication failed")

            # Create a new session
            session_id = str(uuid.uuid4())
            expires_at = datetime.utcnow() + timedelta(seconds=expires_in)

            # Store session data in Redis
            session_key = f"session:{session_id}"
            session_data = {
                "client_id": client_id,
                "token": token,
                "created_at": format_ogx_timestamp(datetime.utcnow()),
                "expires_at": format_ogx_timestamp(expires_at),
                "last_access": format_ogx_timestamp(datetime.utcnow()),
                "access_count": "0",  # Store as string for Redis compatibility
            }

            try:
                # Use Redis pipeline for atomic operations
                redis_client = cast(Redis, self.redis)
                async with redis_client.pipeline() as tr:
                    # Store session data
                    # Convert session_data to have bytes values for Redis
                    str_session_data = {k: str(v).encode() for k, v in session_data.items()}
                    # Use cast to resolve type checker issue
                    await tr.hset(session_key, mapping=cast(Any, str_session_data))

                    # Set expiry on session data
                    await tr.expire(session_key, expires_in)

                    # Add session to client's sessions set
                    await tr.sadd(client_sessions_key, session_id)

                    # Execute all operations
                    await tr.execute()
            except RedisError as e:
                logger.error("Failed to store session data: %s", str(e))
                raise OGxProtocolError(f"Failed to store session data: {str(e)}") from e

            # Log session creation metric
            logger.info(
                "Session created",
                extra={
                    "metric_name": METRIC_SESSION_CREATED,
                    "metric_value": 1,
                    "metric_type": "counter",
                    "metric_tags": {"client_id": client_id},
                },
            )

            # Log current session count
            logger.info(
                "Active sessions",
                extra={
                    "metric_name": METRIC_SESSION_COUNT,
                    "metric_value": session_count + 1,
                    "metric_type": "gauge",
                    "metric_tags": {"client_id": client_id},
                },
            )

            logger.debug("Created session %s for client %s", session_id, client_id)
            return session_id

        except (AuthenticationError, ValidationError):
            # Re-raise authentication and validation errors
            raise
        except Exception as e:
            logger.error("Error creating session: %s", str(e))
            raise OGxProtocolError(f"Failed to create session: {str(e)}") from e

    async def validate_session(self, session_id: str) -> bool:
        """Validate if a session is active and not expired.

        Args:
            session_id: The ID of the session to validate

        Returns:
            bool: True if the session is valid, False otherwise
        """
        logger.debug("Validating session %s", session_id)

        # Check if redis is initialized
        if not self.redis:
            logger.error("Attempted to validate session before initialization")
            return False

        try:
            # Get session data from Redis
            session_key = f"session:{session_id}"
            redis_client = cast(Redis, self.redis)
            session_data = await redis_client.hgetall(session_key)

            if not session_data:
                logger.warning("Session %s not found", session_id)
                return False

            # Check if session has expired
            expires_at = parse_ogx_timestamp(session_data[b"expires_at"].decode())

            if expires_at < datetime.utcnow():
                logger.info("Session %s has expired", session_id)

                # Clean up expired session
                await self.end_session(session_id)
                return False

            # Update last access time and access count
            try:
                async with redis_client.pipeline() as tr:
                    value = format_ogx_timestamp(datetime.utcnow()).encode()
                    await tr.hset(session_key, "last_access", cast(Any, value))
                    await tr.hincrby(session_key, "access_count", 1)
                    await tr.execute()
            except RedisError as e:
                logger.error("Failed to update session data: %s", str(e))
                # Continue validation even if update fails

            logger.debug("Session %s is valid", session_id)
            return True
        except (ValueError, TypeError, KeyError) as e:
            logger.error("Error validating session %s: %s", session_id, str(e))
            return False

    async def refresh_session(self, session_id: str, extend_seconds: Optional[int] = None) -> bool:
        """Refresh the session, extending its expiry time.

        Args:
            session_id: The ID of the session to refresh
            extend_seconds: Optional number of seconds to extend the session by.
                If not provided, uses the default SESSION_TIMEOUT.

        Returns:
            bool: True if the session was refreshed, False if the session was not found
            or could not be refreshed
        """
        logger.debug("Refreshing session %s", session_id)

        # Check if redis is initialized
        if not self.redis:
            logger.error("Attempted to refresh session before initialization")
            return False

        try:
            # Get session data from Redis
            session_key = f"session:{session_id}"
            redis_client = cast(Redis, self.redis)
            session_data = await redis_client.hgetall(session_key)

            if not session_data:
                logger.warning("Session %s not found for refresh", session_id)
                return False

            # Calculate new expiry time
            extend_by = extend_seconds if extend_seconds is not None else SESSION_TIMEOUT
            new_expires_at = datetime.utcnow() + timedelta(seconds=extend_by)

            # Update session data
            try:
                async with redis_client.pipeline() as tr:
                    # Update expiry time
                    new_expires_str = format_ogx_timestamp(new_expires_at)
                    last_access_str = format_ogx_timestamp(datetime.utcnow())

                    mapping_data = {
                        "expires_at": new_expires_str.encode(),
                        "last_access": last_access_str.encode(),
                    }
                    await tr.hset(
                        session_key,
                        mapping=cast(Any, mapping_data),
                    )
                    # Update Redis key expiry
                    await tr.expire(session_key, extend_by)
                    await tr.execute()
            except RedisError as e:
                logger.error("Failed to refresh session %s: %s", session_id, str(e))
                return False

            # Log session refresh metric
            client_id = session_data[b"client_id"].decode()
            logger.info(
                "Session refreshed",
                extra={
                    "metric_name": METRIC_SESSION_RENEWED,
                    "metric_value": 1,
                    "metric_type": "counter",
                    "metric_tags": {"client_id": client_id},
                },
            )

            logger.debug("Session %s refreshed, new expiry: %s", session_id, new_expires_at)
            return True
        except (ValueError, TypeError, KeyError) as e:
            logger.error("Error refreshing session %s: %s", session_id, str(e))
            return False

    async def end_session(self, session_id: str) -> None:
        """End session and clean up Redis data."""
        if not self.redis:
            logger.error("Attempted to end session before initialization")
            raise OGxProtocolError("Session handler not initialized")

        try:
            # Get client ID before deleting session
            session_key = f"session:{session_id}"
            redis_client = cast(Redis, self.redis)
            session_data = await redis_client.hgetall(session_key)
            if not session_data:
                logger.debug("Session %s already ended", session_id)
                return

            client_id = session_data[b"client_id"].decode()
            client_sessions_key = f"client_sessions:{client_id}"

            # Remove session data and from client's active sessions
            tr = redis_client.pipeline()
            await tr.delete(session_key)
            await tr.srem(client_sessions_key, session_id)
            await tr.execute()

            logger.info("Successfully ended session %s", session_id)

            # Log session end metric
            logger.info(
                "Session ended",
                extra={
                    "metric_name": METRIC_SESSION_ENDED,
                    "metric_value": 1,
                    "metric_type": "counter",
                    "metric_tags": {"client_id": client_id},
                },
            )

        except (RedisError, IOError) as e:
            logger.error("Failed to end session %s: %s", session_id, str(e))
            raise OGxProtocolError(f"Failed to end session: {str(e)}") from e

    async def _get_active_sessions(self, client_id: str) -> Set[str]:
        """Get set of active session IDs for client."""
        if not self.redis:
            logger.error("Attempted to get active sessions before initialization")
            return set()

        try:
            client_sessions_key = f"client_sessions:{client_id}"
            redis_client = cast(Redis, self.redis)
            sessions = await redis_client.smembers(client_sessions_key)
            return {s.decode() for s in sessions}
        except (RedisError, IOError) as e:
            logger.error("Failed to get active sessions for client %s: %s", client_id, str(e))
            return set()

    async def _authenticate_with_ogx(self, client_id: str, client_secret: str) -> str:
        """Authenticate with OGx and get bearer token.

        Args:
            client_id: OGx access ID
            client_secret: OGx access password

        Returns:
            str: Bearer token from OGx

        Raises:
            AuthenticationError: If authentication fails
        """
        if not self._protocol_handler:
            logger.error("Attempted to authenticate before protocol handler initialization")
            raise AuthenticationError("Protocol handler not initialized")

        logger.debug("Authenticating client %s with OGx", client_id)
        credentials = {
            "client_id": client_id,
            "client_secret": client_secret,
        }

        try:
            token = await self._protocol_handler.authenticate(credentials)
            logger.debug("Successfully obtained token for client %s", client_id)
            return token
        except (AuthenticationError, ValidationError, RedisError) as e:
            logger.error(
                "OGx authentication failed for client %s: %s",
                client_id,
                str(e),
            )
            raise AuthenticationError(f"OGx authentication failed: {str(e)}") from e

    async def _cleanup_loop(self) -> None:
        """Background task to clean up expired sessions periodically."""
        logger.info("Starting session cleanup task")

        while True:
            logger.debug("Running session cleanup")

            try:
                # Check if redis is initialized
                if not self.redis:
                    logger.error("Redis not initialized in cleanup loop")
                    await asyncio.sleep(CLEANUP_INTERVAL)
                    continue

                redis_client = cast(Redis, self.redis)

                # Get all session keys
                session_keys = await redis_client.keys("session:*")

                for key in session_keys:
                    try:
                        session_id = key.decode().split(":", 1)[1]
                        session_data = await redis_client.hgetall(key)

                        if not session_data:
                            continue

                        # Check if session has expired
                        expires_at = parse_ogx_timestamp(session_data[b"expires_at"].decode())

                        if expires_at < datetime.utcnow():
                            # Get client ID for metrics
                            client_id = session_data[b"client_id"].decode()

                            # Remove session data
                            client_sessions_key = f"client_sessions:{client_id}"
                            async with redis_client.pipeline() as tr:
                                await tr.delete(key)
                                await tr.srem(client_sessions_key, session_id)
                                await tr.execute()

                            logger.info("Cleaned up expired session %s", session_id)

                            # Log session expiry metric
                            logger.info(
                                "Session expired",
                                extra={
                                    "metric_name": METRIC_SESSION_EXPIRED,
                                    "metric_value": 1,
                                    "metric_type": "counter",
                                    "metric_tags": {"client_id": client_id},
                                },
                            )
                    except (ValueError, TypeError, KeyError) as e:
                        logger.error(
                            "Error processing session data for %s: %s", key.decode(), str(e)
                        )
                        continue

            except (RedisError, IOError) as e:
                logger.error("Error in cleanup loop: %s", str(e))

            # Wait before next cleanup
            await asyncio.sleep(CLEANUP_INTERVAL)

    async def close(self) -> None:
        """Cleanup resources when shutting down."""
        logger.info("Shutting down SessionHandler")

        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
                logger.debug("Cleanup task cancelled")
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None

        # Redis client is managed by infrastructure, no need to close it here
        self.redis = None
        logger.info("SessionHandler shutdown complete")
