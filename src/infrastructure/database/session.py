"""Database session configuration.

This module configures the SQLAlchemy session:
- Async engine setup
- Session factory
- Connection pooling

Implementation Notes:
    - Uses SQLAlchemy async engine
    - Configures connection pooling
    - Sets up session factory
"""

import os
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from core.app_settings import get_settings

settings = get_settings()

# Use SQLite for tests, PostgreSQL for development/production
is_test = os.environ.get("TESTING", "").lower() == "true"
database_url = "sqlite+aiosqlite:///:memory:" if is_test else settings.DATABASE_URL

# Create async engine with appropriate configuration
engine_kwargs = {
    "echo": settings.SQL_ECHO,  # SQL query logging
}

if not is_test:
    # Only use connection pooling for non-test environments
    engine_kwargs.update(
        {
            "pool_size": settings.DB_POOL_SIZE,
            "max_overflow": settings.DB_MAX_OVERFLOW,
            "pool_timeout": settings.DB_POOL_TIMEOUT,
        }
    )
else:
    # Use NullPool for SQLite in-memory database in tests
    engine_kwargs["poolclass"] = NullPool

# Create async engine
engine = create_async_engine(database_url, **engine_kwargs)

# Create async session factory
async_session_maker = async_sessionmaker(
    engine,
    expire_on_commit=False,
    autoflush=False,
)
