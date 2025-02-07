"""Redis client for token storage."""

from redis.asyncio import Redis

from core.app_settings import get_settings


async def get_redis_client() -> Redis:
    """Get configured Redis client."""
    settings = get_settings()
    return Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB,
        password=settings.REDIS_PASSWORD,
        decode_responses=True,
    )
