"""Redis client for token storage."""

import asyncio
from typing import Optional

from core.app_settings import get_settings
from core.logging.loggers import get_infra_logger
from redis.asyncio import Redis
from redis.exceptions import ConnectionError

# Get logger
logger = get_infra_logger()

# Global Redis client instance
_redis_client: Optional[Redis] = None


async def get_redis_client() -> Redis:
    """Get configured Redis client with retries.

    Returns:
        Redis: Connected Redis client

    Raises:
        ConnectionError: If unable to connect after retries
    """
    global _redis_client

    if _redis_client is not None:
        return _redis_client

    settings = get_settings()
    max_retries = 5
    retry_delay = 1  # seconds

    for attempt in range(max_retries):
        try:
            _redis_client = Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD,
                decode_responses=True,
            )
            # Test connection
            await _redis_client.ping()
            logger.info("Successfully connected to Redis")
            return _redis_client

        except ConnectionError as e:
            if attempt == max_retries - 1:
                logger.error(f"Failed to connect to Redis after {max_retries} attempts")
                raise
            logger.warning(
                f"Failed to connect to Redis (attempt {attempt + 1}/{max_retries}): {str(e)}"
            )
            await asyncio.sleep(retry_delay * (2**attempt))  # Exponential backoff

        except Exception as e:
            logger.error(f"Unexpected error connecting to Redis: {str(e)}")
            raise
