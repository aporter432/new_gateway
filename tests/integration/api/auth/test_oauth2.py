"""Test OAuth2 authentication dependencies.

This module tests:
- Current user dependency
- Active user checks
- Admin user checks
- Error handling
"""

from datetime import datetime, timedelta
from typing import AsyncGenerator, Dict

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from api.security.jwt import create_access_token
from api.security.oauth2 import get_current_user, get_current_active_user, get_current_admin_user
from infrastructure.database.models import User, UserRole
from infrastructure.database.repositories.user_repository import UserRepository
from infrastructure.database.session import get_session


@pytest.fixture
async def test_user(session: AsyncSession) -> User:
    """Create test user in database.

    Args:
        session: Database session

    Returns:
        Created test user
    """
    user = User(
        email="test@example.com",
        name="Test User",
        hashed_password="hashed_password",
        role=UserRole.USER,
        is_active=True,
    )
    repo = UserRepository(session)
    return await repo.create(user)


@pytest.fixture
async def test_admin(session: AsyncSession) -> User:
    """Create test admin user in database.

    Args:
        session: Database session

    Returns:
        Created admin user
    """
    admin = User(
        email="admin@example.com",
        name="Admin User",
        hashed_password="hashed_password",
        role=UserRole.ADMIN,
        is_active=True,
    )
    repo = UserRepository(session)
    return await repo.create(admin)


@pytest.fixture
async def inactive_user(session: AsyncSession) -> User:
    """Create inactive test user in database.

    Args:
        session: Database session

    Returns:
        Created inactive user
    """
    user = User(
        email="inactive@example.com",
        name="Inactive User",
        hashed_password="hashed_password",
        role=UserRole.USER,
        is_active=False,
    )
    repo = UserRepository(session)
    return await repo.create(user)


@pytest.mark.asyncio
async def test_get_current_user(test_user: User, session: AsyncSession):
    """Test getting current user from valid token."""
    # Create access token for test user
    token = create_access_token({"sub": test_user.email})

    # Get current user
    user = await get_current_user(token, session)
    assert user is not None
    assert user.email == test_user.email
    assert user.role == UserRole.USER


@pytest.mark.asyncio
async def test_get_current_user_invalid_token(session: AsyncSession):
    """Test getting current user with invalid token."""
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user("invalid_token", session)
    assert exc_info.value.status_code == 401
    assert "Could not validate credentials" in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_current_user_nonexistent(session: AsyncSession):
    """Test getting current user with token for nonexistent user."""
    token = create_access_token({"sub": "nonexistent@example.com"})
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(token, session)
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_active_user(test_user: User):
    """Test getting current active user."""
    user = await get_current_active_user(test_user)
    assert user is not None
    assert user.email == test_user.email
    assert user.is_active


@pytest.mark.asyncio
async def test_get_current_active_user_inactive(inactive_user: User):
    """Test getting current active user with inactive user."""
    with pytest.raises(HTTPException) as exc_info:
        await get_current_active_user(inactive_user)
    assert exc_info.value.status_code == 400
    assert "Inactive user" in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_current_admin_user(test_admin: User):
    """Test getting current admin user with admin user."""
    user = get_current_admin_user(test_admin)
    assert user is not None
    assert user.email == test_admin.email
    assert user.role == UserRole.ADMIN


@pytest.mark.asyncio
async def test_get_current_admin_user_non_admin(test_user: User):
    """Test getting current admin user with non-admin user."""
    with pytest.raises(HTTPException) as exc_info:
        get_current_admin_user(test_user)
    assert exc_info.value.status_code == 403
    assert "Not enough permissions" in exc_info.value.detail
