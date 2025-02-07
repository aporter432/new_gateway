"""Configuration settings for the application."""

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings including OGWS credentials."""
    
    OGWS_CLIENT_ID: str
    OGWS_CLIENT_SECRET: str
    OGWS_BASE_URL: str = "https://ogws.orbcomm.com/api/v1.0"
    OGWS_TOKEN_EXPIRY: int = 31536000  # 1 year in seconds
    
    class Config:
        env_file = ".env"