"""Root level test configuration and fixtures.

This module provides base fixtures used across all test types (unit, integration, e2e).
Test-type specific fixtures are located in their respective conftest.py files:
- tests/unit/conftest.py
- tests/integration/conftest.py
- tests/e2e/conftest.py
"""

import os
import sys
import warnings
from pathlib import Path
from typing import Any, AsyncGenerator, Dict

import pytest
from httpx import AsyncClient

from Protexis_Command.core.app_settings import Settings, get_settings

os.environ["TESTING"] = "true"

warnings.filterwarnings("ignore", category=DeprecationWarning, module="passlib.utils")
warnings.filterwarnings("ignore", category=UserWarning, module="passlib.handlers.bcrypt")


ROOT_DIR = Path(__file__).parent.parent
SRC_PATH = str(ROOT_DIR / "Protexis_Command")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

pytest_plugins = ["pytest_asyncio"]


@pytest.fixture
def mock_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    """Configure test environment settings.

    Args:
        monkeypatch: Pytest fixture for modifying environment
    """
    monkeypatch.setenv("OGx_CLIENT_ID", "test_client")
    monkeypatch.setenv("OGx_CLIENT_SECRET", "test_secret")


@pytest.fixture
def mock_redis_client() -> Dict[str, Any]:
    """Provide a mock Redis client for testing.

    Returns:
        Dict[str, Any]: Empty dictionary simulating Redis storage
    """
    return {}


@pytest.fixture(scope="session")
def settings() -> Settings:
    """Provide test settings with validation."""
    settings = get_settings()

    # Validate required settings
    missing = []
    if not settings.OGx_CLIENT_ID:
        missing.append("OGx_CLIENT_ID")
    if not settings.OGx_CLIENT_SECRET:
        missing.append("OGx_CLIENT_SECRET")
    if not settings.OGx_TEST_MOBILE_ID:
        missing.append("OGx_TEST_MOBILE_ID")

    if missing:
        pytest.skip(f"Missing required settings: {', '.join(missing)}")

    return settings


@pytest.fixture(scope="function")
async def http_client() -> AsyncGenerator[AsyncClient, None]:
    """Create an async HTTP client for testing."""
    async with AsyncClient() as client:
        yield client


@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set up environment variables for testing."""
    test_env = {
        "ENVIRONMENT": "test",
        "OGx_BASE_URL": "http://localhost:8080/api/v1.0",  # Default for unit tests
        "OGx_CLIENT_ID": "70000934",
        "OGx_CLIENT_SECRET": "password",
    }
    for key, value in test_env.items():
        monkeypatch.setenv(key, value)
