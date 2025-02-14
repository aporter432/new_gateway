"""Authentication routes for user operations.

This module implements the authentication endpoints:
- Login with email/password
- Token validation
- Session management

Implementation Notes:
    - Uses FastAPI for routing
    - Implements JWT authentication
    - Follows REST API patterns
    - Provides clear error responses
"""

from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas.user import Token
from api.security.jwt import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from api.security.password import verify_password
from infrastructure.database.dependencies import get_db
from infrastructure.database.repositories.user_repository import UserRepository

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Token:
    """Authenticate user and return access token.

    Args:
        form_data: OAuth2 password request form containing email and password
        db: Database session

    Returns:
        Token object containing access token

    Raises:
        HTTPException: If authentication fails
    """
    # Get user from database
    user_repo = UserRepository(db)
    user = await user_repo.get_by_email(
        form_data.username
    )  # OAuth2 form uses username field for email

    # Verify user exists and password is correct
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is disabled",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email},  # Use email as subject claim
        expires_delta=access_token_expires,
    )

    # Return token response
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # Convert to seconds
    )
