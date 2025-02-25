"""Authentication metrics collection."""

from typing import Dict, Optional

from .backends.base import MetricsBackend


class AuthMetrics:
    """Collector for authentication-related metrics."""

    def __init__(self, backend: MetricsBackend):
        """Initialize authentication metrics collector.

        Args:
            backend: Metrics storage backend
        """
        self.backend = backend

    async def record_token_operation(
        self,
        operation: str,
        success: bool,
        token_type: str,
        error_type: Optional[str] = None,
        customer_id: Optional[str] = None,
    ) -> None:
        """Record a token operation (creation, validation, refresh).

        Args:
            operation: Type of operation (create, validate, refresh)
            success: Whether the operation was successful
            token_type: Type of token (access, refresh)
            error_type: Type of error if operation failed
            customer_id: Optional customer ID
        """
        tags: Dict[str, str] = {
            "operation": operation,
            "success": str(success),
            "token_type": token_type,
        }
        if customer_id:
            tags["customer_id"] = customer_id
        if error_type and not success:
            tags["error_type"] = error_type

        # Increment operation counter
        await self.backend.increment("auth_token_operations_total", 1, tags)

    async def record_token_lifetime(
        self,
        token_type: str,
        lifetime_seconds: float,
        customer_id: Optional[str] = None,
    ) -> None:
        """Record token lifetime metrics.

        Args:
            token_type: Type of token (access, refresh)
            lifetime_seconds: Token lifetime in seconds
            customer_id: Optional customer ID
        """
        tags: Dict[str, str] = {"token_type": token_type}
        if customer_id:
            tags["customer_id"] = customer_id

        # Record token lifetime
        await self.backend.histogram(
            "auth_token_lifetime_seconds",
            lifetime_seconds,
            tags,
        )

    async def record_active_sessions(
        self,
        count: int,
        customer_id: Optional[str] = None,
    ) -> None:
        """Record number of active sessions.

        Args:
            count: Number of active sessions
            customer_id: Optional customer ID
        """
        tags: Dict[str, str] = {}
        if customer_id:
            tags["customer_id"] = customer_id

        # Update active sessions gauge
        await self.backend.gauge("auth_active_sessions", count, tags)

    async def record_auth_attempt(
        self,
        success: bool,
        auth_method: str,
        error_type: Optional[str] = None,
        customer_id: Optional[str] = None,
    ) -> None:
        """Record an authentication attempt.

        Args:
            success: Whether the attempt was successful
            auth_method: Authentication method used
            error_type: Type of error if attempt failed
            customer_id: Optional customer ID
        """
        tags: Dict[str, str] = {
            "success": str(success),
            "auth_method": auth_method,
        }
        if customer_id:
            tags["customer_id"] = customer_id
        if error_type and not success:
            tags["error_type"] = error_type

        # Increment auth attempts counter
        await self.backend.increment("auth_attempts_total", 1, tags)
