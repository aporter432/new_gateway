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

# pylint: disable=no-member

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool
from sqlalchemy.engine import Connection

from core.app_settings import get_settings
from infrastructure.database.models.base import Base

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
    settings = get_settings()
    return settings.database_url


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


def do_run_migrations(connection: Connection) -> None:
    """Run migrations with the given connection.

    Args:
        connection: Database connection to use
    """
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations asynchronously."""
    configuration = config.get_section(config.config_ini_section)
    if configuration is not None:
        configuration["sqlalchemy.url"] = get_database_url()

        connectable = engine_from_config(
            configuration,
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
        )

        with connectable.connect() as connection:
            await connection.run_sync(do_run_migrations)

        await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode using async support."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
