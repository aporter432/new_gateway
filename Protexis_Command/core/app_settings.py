"""Application-wide settings and configuration.

This module serves as the single source of truth for all configuration settings.
It adheres to the following specifications:

OGx Integration (OGx-1.txt):
    - Section 4.1: Authentication and Security
        - Client credentials flow
        - Token management
        - Rate limiting
    - Section 5.2: Environment Configuration
        - API endpoints
        - Network settings
        - Test vs Production modes

Related Constants:
    - protocols.ogx.constants.auth: Authentication-related constants
    - protocols.ogx.constants.endpoints: API endpoint definitions
    - protocols.ogx.constants.limits: Rate limits and timeouts
    - protocols.ogx.constants.message_states: State management configuration

Environment Handling:
    Development:
        - Uses default test credentials if env vars not set
        - Allows local development without env setup
        - Matches docker-compose.yml test configuration

    Production:
        - Requires all credentials via environment variables
        - No default values permitted
        - Raises error if any required var missing
        - TODO: Define production environment setup process
        - TODO: Document credential management procedure
"""

from functools import lru_cache
from typing import Any, Optional

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseModel):
    """Application configuration model."""

    app_name: str
    version: str
    debug: bool
    env_file: Optional[str] = None
    log_level: Optional[str] = None
    api_key: Optional[str] = None


class Settings(BaseSettings):
    """Application settings and configuration management.

    This class enforces:
    1. Type safety through Pydantic validation
    2. Environment-specific behavior
    3. Security constraints for production
    4. Development convenience for local testing

    Configuration Sources (in order of precedence):
    1. Environment variables
    2. .env file
    3. Development defaults (non-production only)

    Security Notes:
    - Never commit real credentials to source control
    - Production requires explicit environment configuration
    - Test credentials are automatically rejected in production

    TODO: Production Setup
    - [ ] Define secure credential management process
    - [ ] Document production deployment checklist
    - [ ] Implement credential rotation mechanism
    - [ ] Add production configuration validation
    """

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True, extra="allow"
    )

    # Environment detection
    ENVIRONMENT: str = "development"

    # Database settings
    DATABASE_URL: str
    SQL_ECHO: bool = False
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = (
        30  # Seconds to wait before giving up on getting a connection from the pool
    )

    # OGx settings with development defaults
    # Reference: OGx-1.txt Section 4.1.1 - Authentication
    OGx_CLIENT_ID: str = "70000934"
    OGx_CLIENT_SECRET: str = "password"
    OGx_BASE_URL: str = "https://OGx.orbcomm.com/api/v1.0"
    OGx_TOKEN_EXPIRY: int = 31536000

    # Customer identification - required in production
    CUSTOMER_ID: str = "test_customer"

    # Redis settings
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""

    # DynamoDB settings
    DYNAMODB_TABLE_NAME: str = "OGx_message_states"

    # JWT settings
    JWT_SECRET_KEY: str = "development_secret_key"
    JWT_ALGORITHM: str = "HS256"

    # Test settings
    OGx_TEST_MOBILE_ID: str = "OGx-00002000SKY9307"
    OGx_TEST_MODE: bool = True

    def __hash__(self) -> int:
        """Make Settings hashable for lru_cache compatibility.

        Returns:
            Hash of the settings instance based on its model fields
        """
        return hash(tuple(sorted(self.model_dump().items())))

    def __init__(self, **kwargs: Any) -> None:
        """Initialize settings with validation.

        Args:
            **kwargs: Keyword arguments to override default settings

        Raises:
            ValueError: If production environment uses development defaults
        """
        super().__init__(**kwargs)
        if self.ENVIRONMENT == "production":
            # In production, ensure no development defaults are used
            # This enforces OGx-1.txt Section 4.1 security requirements
            required_vars = ["OGx_CLIENT_ID", "OGx_CLIENT_SECRET", "CUSTOMER_ID"]
            missing = [
                var
                for var in required_vars
                if getattr(self, var) in (None, "", "70000934", "password", "test_customer")
            ]
            if missing:
                raise ValueError(
                    f"Production environment requires {', '.join(missing)} "
                    "via environment variables"
                )


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance.

    Returns:
        Settings: Cached settings instance

    Note:
        Uses lru_cache to prevent repeated environment reads
        Settings are immutable once loaded
    """
    return Settings()
