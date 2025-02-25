"""Factory functions for creating API clients."""

from functools import lru_cache
from typing import Optional

from ...api.services.auth.manager import OGxAuthManager
from ...api.services.ogx_client import OGxClient
from ...core.settings.app_settings import Settings, get_settings
from ...infrastructure.cache.redis import get_redis_client


@lru_cache
async def get_OGx_client(settings: Optional[Settings] = None) -> OGxClient:
    """Get configured OGx client instance.

    Args:
        settings: Optional settings instance. If not provided, will use default settings.

    Returns:
        Configured OGx client instance
    """
    if settings is None:
        settings = get_settings()

    redis = await get_redis_client()
    auth_manager = OGxAuthManager(settings, redis)
    return OGxClient(auth_manager, settings)
