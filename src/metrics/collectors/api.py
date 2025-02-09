"""API metrics collection."""

from typing import Dict, Optional

from ..backends.base import MetricsBackend


class APIMetrics:
    """Collector for API-related metrics."""

    def __init__(self, backend: MetricsBackend):
        """Initialize API metrics collector.

        Args:
            backend: Metrics storage backend
        """
        self.backend = backend

    async def record_request(
        self,
        method: str,
        path: str,
        status_code: int,
        duration: float,
        customer_id: Optional[str] = None,
    ) -> None:
        """Record an API request.

        Args:
            method: HTTP method
            path: Request path
            status_code: Response status code
            duration: Request duration in seconds
            customer_id: Optional customer ID
        """
        tags: Dict[str, str] = {
            "method": method,
            "path": path,
            "status": str(status_code),
        }
        if customer_id:
            tags["customer_id"] = customer_id

        # Increment request counter
        await self.backend.increment("api_requests_total", 1, tags)

        # Record request duration
        await self.backend.histogram("api_request_duration_seconds", duration, tags)

        # Track concurrent requests
        await self.backend.gauge("api_requests_in_progress", 1, tags)

    async def record_error(
        self,
        method: str,
        path: str,
        error_type: str,
        customer_id: Optional[str] = None,
    ) -> None:
        """Record an API error.

        Args:
            method: HTTP method
            path: Request path
            error_type: Type of error
            customer_id: Optional customer ID
        """
        tags: Dict[str, str] = {
            "method": method,
            "path": path,
            "error_type": error_type,
        }
        if customer_id:
            tags["customer_id"] = customer_id

        await self.backend.increment("api_errors_total", 1, tags)
