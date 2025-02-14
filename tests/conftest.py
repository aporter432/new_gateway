"""Test configuration and fixtures for unit testing FastAPI login functionality."""

import asyncio
import os
import sys
import warnings
from pathlib import Path
from typing import Any, Dict, AsyncGenerator

# Set test environment before any imports
os.environ["TESTING"] = "true"

# Filter out specific warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, module="passlib.utils")
warnings.filterwarnings("ignore", category=UserWarning, module="passlib.handlers.bcrypt")

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, AsyncConnection, create_async_engine

# Add src to Python path for all tests
ROOT_DIR = Path(__file__).parent.parent
SRC_PATH = str(ROOT_DIR / "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

# Configure pytest-asyncio
pytest_plugins = ["pytest_asyncio"]

# Import after setting test environment
from infrastructure.database.models.base import Base
from infrastructure.database.models.user import User  # noqa: E402
from infrastructure.database.session import database_url


@pytest.fixture(scope="function")
async def db_engine():
    """Create a new engine for each test function."""
    engine = create_async_engine(database_url)
    yield engine
    await engine.dispose()


@pytest.fixture(scope="function")
async def db_connection(db_engine) -> AsyncGenerator[AsyncConnection, None]:
    """Create a database connection for each test.

    Creates all tables before tests and drops them after.
    """
    async with db_engine.connect() as conn:
        await conn.run_sync(Base.metadata.create_all)
        yield conn
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture()
async def db_session(db_connection: AsyncConnection) -> AsyncGenerator[AsyncSession, None]:
    """Provide a database session for test isolation.

    Args:
        db_connection: Database connection from the function-scoped fixture

    Yields:
        AsyncSession: Database session that's cleaned up after each test
    """
    async with AsyncSession(bind=db_connection, expire_on_commit=False) as session:
        # Start with a clean slate for each test
        for table in reversed(Base.metadata.sorted_tables):
            await session.execute(table.delete())
        await session.commit()

        yield session

        # Clean up after the test
        await session.rollback()
        for table in reversed(Base.metadata.sorted_tables):
            await session.execute(table.delete())
        await session.commit()


@pytest.fixture
def mock_redis_client() -> Dict[str, Any]:
    """Provide a mock Redis client for testing.

    Returns:
        Dict[str, Any]: Empty dictionary simulating Redis storage
    """
    return {}


@pytest.fixture
def mock_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    """Configure test environment settings.

    Args:
        monkeypatch: Pytest fixture for modifying environment
    """
    monkeypatch.setenv("OGWS_CLIENT_ID", "test_client")
    monkeypatch.setenv("OGWS_CLIENT_SECRET", "test_secret")
