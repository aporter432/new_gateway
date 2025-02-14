"""Test configuration and fixtures for unit testing FastAPI login functionality."""

import asyncio
import os
import sys
import warnings
from pathlib import Path
from typing import Any, Dict, Generator

import pytest
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncSession, create_async_engine

from core.app_settings import Settings, get_settings

os.environ["TESTING"] = "true"

warnings.filterwarnings("ignore", category=DeprecationWarning, module="passlib.utils")
warnings.filterwarnings("ignore", category=UserWarning, module="passlib.handlers.bcrypt")


ROOT_DIR = Path(__file__).parent.parent
SRC_PATH = str(ROOT_DIR / "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

pytest_plugins = ["pytest_asyncio"]


@pytest.fixture
def mock_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    """Configure test environment settings.

    Args:
        monkeypatch: Pytest fixture for modifying environment
    """
    monkeypatch.setenv("OGWS_CLIENT_ID", "test_client")
    monkeypatch.setenv("OGWS_CLIENT_SECRET", "test_secret")


@pytest.fixture
def mock_redis_client() -> Dict[str, Any]:
    """Provide a mock Redis client for testing.

    Returns:
        Dict[str, Any]: Empty dictionary simulating Redis storage
    """
    return {}


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def settings() -> Settings:
    """Provide test settings with validation."""
    settings = get_settings()

    # Validate required settings
    missing = []
    if not settings.OGWS_CLIENT_ID:
        missing.append("OGWS_CLIENT_ID")
    if not settings.OGWS_CLIENT_SECRET:
        missing.append("OGWS_CLIENT_SECRET")
    if not settings.OGWS_TEST_MOBILE_ID:
        missing.append("OGWS_TEST_MOBILE_ID")

    if missing:
        pytest.skip(f"Missing required settings: {', '.join(missing)}")

    return settings
