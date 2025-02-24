"""Rate limiting middleware for the OGx API.

This module implements rate limiting as specified in OGx-1.txt Section 3.2.
It uses Redis to track and enforce rate limits across multiple API instances.
"""

from datetime import datetime, timedelta
from typing import Callable, Dict, Optional

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from redis import Redis
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from Protexis_Command.core.app_settings import Settings, get_settings


class RateLimitConfig:
    """Rate limit configuration per endpoint type."""

    def __init__(
        self,
        requests_per_minute: int,
        burst_size: Optional[int] = None,
        key_prefix: str = "rate_limit",
    ):
        """Initialize rate limit configuration.

        Args:
            requests_per_minute: Maximum requests allowed per minute
            burst_size: Optional burst size for temporary spikes
            key_prefix: Redis key prefix for rate limit tracking
        """
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size or requests_per_minute
        self.key_prefix = key_prefix


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for enforcing API rate limits."""

    def __init__(
        self,
        app: ASGIApp,
        redis_url: str,
        settings: Settings = get_settings(),
    ):
        """Initialize rate limit middleware.

        Args:
            app: The ASGI application
            redis_url: Redis connection URL
            settings: Application settings
        """
        super().__init__(app)
        self.redis = Redis.from_url(redis_url)
        self.settings = settings
        self.limits: Dict[str, RateLimitConfig] = {
            "default": RateLimitConfig(
                requests_per_minute=60,
                burst_size=120,
                key_prefix="rate_limit:default",
            ),
            "submit": RateLimitConfig(
                requests_per_minute=30,
                burst_size=60,
                key_prefix="rate_limit:submit",
            ),
            "query": RateLimitConfig(
                requests_per_minute=120,
                burst_size=240,
                key_prefix="rate_limit:query",
            ),
        }

    def get_rate_limit_key(self, request: Request) -> str:
        """Generate Redis key for rate limit tracking.

        Args:
            request: The incoming request

        Returns:
            str: Redis key combining client ID and endpoint type
        """
        client_id = request.headers.get("X-Client-ID", "anonymous")
        path = request.url.path.lower()

        if "submit" in path:
            limit_type = "submit"
        elif "get" in path or "info" in path:
            limit_type = "query"
        else:
            limit_type = "default"

        return f"{self.limits[limit_type].key_prefix}:{client_id}"

    async def check_rate_limit(self, key: str, config: RateLimitConfig) -> bool:
        """Check if request is within rate limits.

        Args:
            key: Redis key for tracking
            config: Rate limit configuration

        Returns:
            bool: True if request is allowed, False if rate limited
        """
        pipe = self.redis.pipeline()
        now = datetime.utcnow()
        window_start = now - timedelta(minutes=1)

        # Remove old requests from the sorted set
        pipe.zremrangebyscore(key, 0, window_start.timestamp())

        # Count requests in the current window
        pipe.zcard(key)

        # Add current request
        pipe.zadd(key, {now.timestamp(): now.timestamp()})

        # Set key expiration
        pipe.expire(key, 60)

        results = pipe.execute()
        request_count = results[1]

        return request_count < config.burst_size

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request through rate limiting.

        Args:
            request: The incoming request
            call_next: Next middleware in chain

        Returns:
            Response: The HTTP response
        """
        key = self.get_rate_limit_key(request)
        limit_type = "submit" if "submit" in request.url.path.lower() else "default"
        config = self.limits[limit_type]

        if not await self.check_rate_limit(key, config):
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded",
                    "limit": config.requests_per_minute,
                    "retry_after": 60,
                },
            )

        response = await call_next(request)
        return response


def add_rate_limit_middleware(app: FastAPI, redis_url: str) -> None:
    """Register rate limiting middleware with FastAPI app.

    Args:
        app: The FastAPI application
        redis_url: Redis connection URL
    """
    app.add_middleware(RateLimitMiddleware, redis_url=redis_url)
