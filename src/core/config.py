"""Configuration settings for the application."""

from functools import lru_cache
from os import environ

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings including OGWS credentials."""

    OGWS_CLIENT_ID: str
    OGWS_CLIENT_SECRET: str
    OGWS_BASE_URL: str = "https://ogws.orbcomm.com/api/v1.0"
    OGWS_TOKEN_EXPIRY: int = 31536000  # 1 year in seconds

    # Redis settings
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings.

    Raises:
        ValueError: If required environment variables are missing
    """
    if "OGWS_CLIENT_ID" not in environ:
        raise ValueError("OGWS_CLIENT_ID environment variable is required")
    if "OGWS_CLIENT_SECRET" not in environ:
        raise ValueError("OGWS_CLIENT_SECRET environment variable is required")

    return Settings(
        OGWS_CLIENT_ID=environ["OGWS_CLIENT_ID"], OGWS_CLIENT_SECRET=environ["OGWS_CLIENT_SECRET"]
    )
