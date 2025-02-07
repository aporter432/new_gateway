"""Application-wide settings and configuration.

This module handles:
- OGWS API credentials and configuration
- Redis connection settings
- Environment-based configuration
"""

from functools import lru_cache
from os import environ

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings including OGWS credentials."""

    # OGWS settings
    OGWS_CLIENT_ID: str
    OGWS_CLIENT_SECRET: str
    OGWS_BASE_URL: str = "https://ogws.orbcomm.com/api/v1.0"
    OGWS_TOKEN_EXPIRY: int = 31536000  # 1 year in seconds

    # Test settings
    OGWS_TEST_MOBILE_ID: str = "OGx-00002000SKY9307"  # Default test mobile ID
    OGWS_TEST_MODE: bool = False  # Whether to use test endpoints

    # Customer identification
    CUSTOMER_ID: str  # Required for logging context

    # Redis settings
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
