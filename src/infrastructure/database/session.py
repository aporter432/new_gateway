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

import logging
import os
import socket
import subprocess
from urllib.parse import urlparse

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from core.app_settings import get_settings

settings = get_settings()

# Use SQLite for tests, PostgreSQL for development/production
is_test = os.environ.get("TESTING", "").lower() == "true"
database_url = "sqlite+aiosqlite:///:memory:" if is_test else settings.DATABASE_URL

# Add debug logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

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

# In the session creation:
logger.debug(f"Creating database session with URL: {database_url}")

# Debug connection details
try:
    parsed_url = urlparse(database_url)
    logger.debug(f"Parsed database URL - Host: {parsed_url.hostname}, Port: {parsed_url.port}")

    # Try DNS resolution
    db_ip = socket.gethostbyname(parsed_url.hostname)
    logger.debug(f"Resolved {parsed_url.hostname} to {db_ip}")

    # Try TCP connection
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    result = sock.connect_ex((db_ip, parsed_url.port or 5432))
    if result == 0:
        logger.debug(f"Successfully connected to {db_ip}:{parsed_url.port or 5432}")
    else:
        logger.error(f"Failed to connect to {db_ip}:{parsed_url.port or 5432}")
    sock.close()
except Exception as e:
    logger.error(f"Connection test failed: {str(e)}")

# After the database_url definition
logger.debug(f"Testing database connection to: {database_url}")

try:
    # Try to ping the database host
    result = subprocess.run(["ping", "-c", "1", "db"], capture_output=True, text=True)
    logger.debug(f"Ping result: {result.stdout}")

    # Try to get host info
    host_info = socket.gethostbyname_ex("db")
    logger.debug(f"Host info: {host_info}")

except Exception as e:
    logger.error(f"Network test failed: {str(e)}")
