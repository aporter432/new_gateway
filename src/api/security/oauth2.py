"""OAuth2 password flow implementation.

This module provides:
- OAuth2 password flow scheme
- User authentication
- Dependency injection for current user
"""

from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from api.security.jwt import TokenData, verify_token
from infrastructure.database.dependencies import get_db
from infrastructure.database.models import User
from infrastructure.database.repositories.user_repository import UserRepository

# OAuth2 scheme configuration
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_db),
) -> User:
    """Get current authenticated user.

    Args:
        token: JWT token from request
        session: Database session

    Returns:
        Current authenticated user

    Raises:
        HTTPException: If token is invalid, missing email, or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Verify token expiration
        token_data: TokenData = verify_token(token)

        # Validate email presence
        if token_data.email is None:
            raise credentials_exception

        # Get user from database
        user_repo = UserRepository(session)
        user = await user_repo.get_by_email(token_data.email)
        if user is None:
            raise credentials_exception

        return user

    except Exception:
        raise credentials_exception


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Get current active user.

    Args:
        current_user: Current authenticated user

    Returns:
        Current active user

    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def get_current_admin_user(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Get current admin user.

    Args:
        current_user: Current active user

    Returns:
        Current admin user

    Raises:
        HTTPException: If user is not an admin
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    return current_user
