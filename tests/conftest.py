"""Test configuration and fixtures."""

import sys
from pathlib import Path
from typing import Any, Dict

import pytest

# Add src to Python path for all tests
root_dir = Path(__file__).parent.parent
src_path = str(root_dir / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)


@pytest.fixture
def mock_redis_client() -> Dict[str, Any]:
    """Provide mock Redis client."""
    return {}


@pytest.fixture
def mock_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    """Provide mock settings."""
    monkeypatch.setenv("OGWS_CLIENT_ID", "test_client")
    monkeypatch.setenv("OGWS_CLIENT_SECRET", "test_secret")
