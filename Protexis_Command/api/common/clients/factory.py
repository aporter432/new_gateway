"""Factory functions for creating API clients."""

from functools import lru_cache
from typing import Optional

from Protexis_Command.api.services.auth.manager import OGxAuthManager
from Protexis_Command.api.services.ogx_client import OGxClient
from Protexis_Command.core.settings.app_settings import Settings, get_settings
from Protexis_Command.infrastructure.cache.redis import get_redis_client


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
