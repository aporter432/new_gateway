"""Redis client for token storage."""

from typing import Optional

from redis import Redis


async def get_redis_client() -> Redis:
    """Get configured Redis client."""
