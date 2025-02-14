"""Unit tests for login endpoint.

This module tests the login functionality:
- Successful login
- Invalid credentials
- Disabled account
- Missing fields
"""

import warnings
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

# Filter warnings before imports
warnings.filterwarnings("ignore", category=Warning, module="passlib")
warnings.filterwarnings("ignore", category=DeprecationWarning)

from api.routes.auth import router
from api.security.password import get_password_hash
from core.app_settings import Settings
from infrastructure.database.dependencies import get_db
from infrastructure.database.models import Base, User, UserRole  # noqa: F401
from infrastructure.database.repositories.user_repository import UserRepository
from infrastructure.database.session import database_url as TEST_DATABASE_URL


@pytest.fixture()
def app(db_session: AsyncSession) -> FastAPI:
    """Create test FastAPI instance with test database.

    Args:
        db_session: Database session from fixture

    Returns:
        FastAPI: Test application instance
    """
    # Create test app
    test_app = FastAPI()
    test_app.include_router(router)

    # Override the get_db dependency to use our test session
    async def override_get_db():
        yield db_session

    test_app.dependency_overrides[get_db] = override_get_db

    return test_app


@pytest.fixture()
def client(app: FastAPI) -> TestClient:
    """Provide an HTTP client for FastAPI app testing."""
    return TestClient(app)


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create test user in database.

    Args:
        db_session: Database session

    Returns:
        Created test user
    """
    user = User(
        email="test@example.com",
        name="Test User",
        hashed_password=get_password_hash("testpassword123!"),
        is_active=True,
    )
    repo = UserRepository(db_session)
    return await repo.create(user)


@pytest.mark.asyncio
async def test_login_success(test_user: User, client: TestClient) -> None:
    """Test successful login with valid credentials.

    Args:
        test_user: Test user fixture
        client: Test client
    """
    response = client.post(
        "/auth/login",
        data={
            "username": test_user.email,
            "password": "testpassword123!",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert isinstance(data["expires_in"], int)


@pytest.mark.asyncio
async def test_login_invalid_password(test_user: User, client: TestClient) -> None:
    """Test login with invalid password.

    Args:
        test_user: Test user fixture
        client: Test client
    """
    response = client.post(
        "/auth/login",
        data={
            "username": test_user.email,
            "password": "wrongpassword",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"


@pytest.mark.asyncio
async def test_login_inactive_user(
    test_user: User, db_session: AsyncSession, client: TestClient
) -> None:
    """Test login with inactive user account.

    Args:
        test_user: Test user fixture
        db_session: Database session
        client: Test client
    """
    # Deactivate user
    test_user.is_active = False
    repo = UserRepository(db_session)
    await repo.update(test_user)

    response = client.post(
        "/auth/login",
        data={
            "username": test_user.email,
            "password": "testpassword123!",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "User account is disabled"


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: TestClient) -> None:
    """Test login with non-existent user.

    Args:
        client: Test client
    """
    response = client.post(
        "/auth/login",
        data={
            "username": "nonexistent@example.com",
            "password": "somepassword",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"


@pytest.mark.asyncio
async def test_login_missing_fields(client: TestClient) -> None:
    """Test login with missing required fields.

    Args:
        client: Test client
    """
    response = client.post("/auth/login", data={})

    assert response.status_code == 422  # Unprocessable Entity
