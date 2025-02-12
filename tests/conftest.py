"""Test configuration and fixtures."""

import sys
from pathlib import Path
from typing import Any, Dict

import pytest
import pytest_asyncio

# Add src to Python path for all tests
root_dir = Path(__file__).parent.parent
src_path = str(root_dir / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)


# Configure pytest-asyncio
pytest_plugins = ["pytest_asyncio"]


@pytest.fixture
def mock_redis_client() -> Dict[str, Any]:
    """Provide mock Redis client."""
    return {}


@pytest.fixture
def mock_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    """Provide mock settings."""
    monkeypatch.setenv("OGWS_CLIENT_ID", "test_client")
    monkeypatch.setenv("OGWS_CLIENT_SECRET", "test_secret")
