"""Factory functions for creating API clients."""

from functools import lru_cache
from typing import Optional

from core.app_settings import Settings, get_settings
from protocols.ogx.auth.manager import OGWSAuthManager
from infrastructure.redis import get_redis_client

from .ogws import OGWSClient


@lru_cache
async def get_ogws_client(settings: Optional[Settings] = None) -> OGWSClient:
    """Get configured OGWS client instance.

    Args:
        settings: Optional settings instance. If not provided, will use default settings.

    Returns:
        Configured OGWS client instance
    """
    if settings is None:
        settings = get_settings()

    redis = await get_redis_client()
    auth_manager = OGWSAuthManager(settings, redis)
    return OGWSClient(auth_manager, settings)
