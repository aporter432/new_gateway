"""Redis client for token storage."""

import asyncio
import sys
from typing import Optional

from redis.asyncio import Redis

from Protexis_Command.core.logging.loggers import get_infra_logger
from Protexis_Command.core.settings.app_settings import get_settings

# Get logger
logger = get_infra_logger()

# Redis client instance (module-level)
_redis_client: Optional[Redis] = None


def get_redis_url() -> str:
    """Get Redis URL from settings.

    Returns:
        str: Formatted Redis URL
    """
    settings = get_settings()

    # Build the authentication part (if password is provided)
    auth = f":{settings.REDIS_PASSWORD}@" if settings.REDIS_PASSWORD else ""

    # Construct the full URL
    return f"redis://{auth}{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"


async def get_redis_client() -> Redis:
    """Get configured Redis client with retries.

    Returns:
        Redis: Connected Redis client

    Raises:
        ConnectionError: If unable to connect after retries
    """
    # Access module-level variable without using global keyword
    if _redis_client is not None:
        return _redis_client

    settings = get_settings()
    max_retries = 5
    retry_delay = 1  # seconds

    for attempt in range(max_retries):
        try:
            client = Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD,
                decode_responses=True,
            )
            # Test connection
            await client.ping()
            logger.info("Successfully connected to Redis")
            # Set module variable using module name to avoid global statement
            this_module = sys.modules[__name__]
            setattr(this_module, "_redis_client", client)
            return client

        except ConnectionError as e:
            if attempt == max_retries - 1:
                logger.error(f"Failed to connect to Redis after {max_retries} attempts")
                error_msg = f"Could not connect to Redis after {max_retries} attempts"
                raise ConnectionError(error_msg) from e

            logger.warning(
                f"Failed to connect to Redis (attempt {attempt + 1}/{max_retries}): {str(e)}"
            )
            await asyncio.sleep(retry_delay * (2**attempt))  # Exponential backoff

        except Exception as e:
            logger.error(f"Unexpected error connecting to Redis: {str(e)}")
            raise

    # This should never happen, but ensures the function always returns or raises
    raise ConnectionError("Failed to connect to Redis - loop completed without success")
