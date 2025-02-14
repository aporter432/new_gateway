"""Test OAuth2 authentication functionality.

This module tests:
- Current user validation
- Active user validation
- Admin user validation
- Token verification
"""

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt
from datetime import datetime, timedelta

from api.security.jwt import create_access_token, ALGORITHM
from api.security.oauth2 import get_current_user, get_current_active_user, get_current_admin_user
from infrastructure.database.models import User, UserRole
from infrastructure.database.repositories.user_repository import UserRepository
from core.app_settings import get_settings

settings = get_settings()


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create test user in database."""
    user = User(
        email="test@example.com",
        name="Test User",
        hashed_password="dummy_hash",  # Not used in these tests
        is_active=True,
        role=UserRole.USER,
    )
    repo = UserRepository(db_session)
    return await repo.create(user)


@pytest.fixture
async def test_admin(db_session: AsyncSession) -> User:
    """Create test admin user in database."""
    admin = User(
        email="admin@example.com",
        name="Admin User",
        hashed_password="dummy_hash",  # Not used in these tests
        is_active=True,
        role=UserRole.ADMIN,
    )
    repo = UserRepository(db_session)
    return await repo.create(admin)


@pytest.mark.asyncio
async def test_get_current_user_success(test_user: User, db_session: AsyncSession):
    """Test successful current user retrieval."""
    token = create_access_token({"sub": test_user.email})
    user = await get_current_user(token, db_session)
    assert user.email == test_user.email


@pytest.mark.asyncio
async def test_get_current_user_invalid_token(db_session: AsyncSession):
    """Test current user retrieval with invalid token."""
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user("invalid_token", db_session)
    assert exc_info.value.status_code == 401
    assert "Could not validate credentials" in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_current_user_nonexistent(db_session: AsyncSession):
    """Test current user retrieval with non-existent user."""
    token = create_access_token({"sub": "nonexistent@example.com"})
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(token, db_session)
    assert exc_info.value.status_code == 401
    assert "Could not validate credentials" in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_current_user_missing_email(db_session: AsyncSession):
    """Test current user retrieval with token missing email claim."""
    # Create token with valid exp but no sub claim
    token = jwt.encode(
        {
            # Omit sub claim entirely
            "exp": int((datetime.utcnow() + timedelta(minutes=15)).timestamp())
        },
        settings.JWT_SECRET_KEY,
        algorithm=ALGORITHM,
    )
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(token, db_session)
    assert exc_info.value.status_code == 401
    assert "Could not validate credentials" in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_current_active_user_success(test_user: User, db_session: AsyncSession):
    """Test successful active user retrieval."""
    user = await get_current_active_user(test_user)
    assert user.email == test_user.email


@pytest.mark.asyncio
async def test_get_current_active_user_inactive(test_user: User, db_session: AsyncSession):
    """Test active user retrieval with inactive user."""
    test_user.is_active = False
    with pytest.raises(HTTPException) as exc_info:
        await get_current_active_user(test_user)
    assert exc_info.value.status_code == 400
    assert "Inactive user" in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_current_admin_user_success(test_admin: User):
    """Test successful admin user validation."""
    admin = get_current_admin_user(test_admin)
    assert admin.email == test_admin.email


@pytest.mark.asyncio
async def test_get_current_admin_user_not_admin(test_user: User):
    """Test admin validation with non-admin user."""
    with pytest.raises(HTTPException) as exc_info:
        get_current_admin_user(test_user)
    assert exc_info.value.status_code == 403
    assert "Not enough permissions" in exc_info.value.detail
