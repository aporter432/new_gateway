"""Redis client for token storage."""

from redis import Redis
from typing import Optional

async def get_redis_client() -> Redis:
    """Get configured Redis client."""