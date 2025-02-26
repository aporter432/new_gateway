"""Alembic environment configuration.

This module configures the Alembic migration environment:
- Database connection
- Migration context
- Model metadata
- Async support

Environment Handling:
    Development:
        - Local PostgreSQL (from docker-compose)
        - Debug logging
        - Flexible validation

    Production:
        - AWS RDS
        - Production logging
        - Strict validation
"""

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool

from Protexis_Command.infrastructure.database.models.base import Base

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Set up logging (if configured)
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set target metadata for migrations
target_metadata = Base.metadata


def get_database_url() -> str:
    """Get database URL based on environment.

    Returns:
        Database URL for current environment
    """
    # Convert async URL to sync URL for Alembic
    url = os.environ.get("DATABASE_URL", "")
    if url.startswith("postgresql+asyncpg://"):
        url = url.replace("postgresql+asyncpg://", "postgresql://")
    return url


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.
    """
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    url = get_database_url()
    connectable = create_engine(
        url,
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
