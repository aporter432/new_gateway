"""FastAPI middleware for collecting API metrics."""

import time
from typing import Callable, Optional

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

from Protexis_Command.infrastructure.metrics import APIMetrics


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware for collecting API metrics in FastAPI applications."""

    def __init__(
        self,
        app: ASGIApp,
        metrics: APIMetrics,
        should_record_path: Callable[[str], bool] = lambda _: True,
        exclude_paths: Optional[list[str]] = None,
    ):
        """Initialize the metrics middleware.

        Args:
            app: The FastAPI application
            metrics: API metrics collector
            should_record_path: Optional function to determine if a path should be recorded
            exclude_paths: Optional list of paths to exclude from metrics
        """
        super().__init__(app)
        self.metrics = metrics
        self.should_record_path = should_record_path
        self.exclude_paths = exclude_paths or []

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Process the request and record metrics.

        Args:
            request: The incoming request
            call_next: The next middleware/endpoint to call

        Returns:
            The response from the next middleware/endpoint
        """
        # Skip excluded paths
        if request.url.path in self.exclude_paths:
            return await call_next(request)

        # Skip if path should not be recorded
        if not self.should_record_path(request.url.path):
            return await call_next(request)

        start_time = time.time()
        status_code = 500  # Default if something goes wrong
        error_type = None

        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        except Exception as e:
            error_type = e.__class__.__name__
            raise
        finally:
            duration = time.time() - start_time

            # Record request metrics
            await self.metrics.record_request(
                duration=duration,
                status_code=status_code,
                method=request.method,
                path=request.url.path,
            )

            # Record error if applicable
            if error_type or status_code >= 400:
                await self.metrics.record_error(
                    error_type=error_type or f"HTTP{status_code}",
                    method=request.method,
                    path=request.url.path,
                )


def add_metrics_middleware(
    app: FastAPI,
    metrics: APIMetrics,
    exclude_paths: Optional[list[str]] = None,
) -> None:
    """Add metrics middleware to a FastAPI application.

    Args:
        app: The FastAPI application
        metrics: API metrics collector
        exclude_paths: Optional list of paths to exclude from metrics
    """
    app.add_middleware(
        MetricsMiddleware,
        metrics=metrics,
        exclude_paths=exclude_paths or ["/metrics", "/health"],
    )
