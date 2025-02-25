"""Authentication routes for user operations.

This module implements the core authentication endpoints for the gateway application.
It handles user registration, login, and token management following OAuth2 with JWT.

Key Components:
    - User Registration: New user signup with email validation
    - Authentication: Email/password login with JWT token generation
    - Session Management: Token-based session handling
    - Role Management: Basic role assignment (expandable for RBAC)

Related Files:
    - Protexis_Command/api_protexis/schemas/user.py: Pydantic models for request/response validation
    - Protexis_Command/api_protexis/security/jwt.py: JWT token generation and validation
    - Protexis_Command/api_protexis/security/password.py: Password hashing and verification
    - Protexis_Command/infrastructure/database/models/user.py: SQLAlchemy User model
    - Protexis_Command/infrastructure/database/repositories/user_repository.py: User database operations

Future RBAC Considerations:
    - Role hierarchy implementation
    - Permission-based access control
    - Role-specific endpoints and middleware
    - Admin interface for role management
    - Role assignment and modification endpoints

Implementation Notes:
    - Uses FastAPI for routing and dependency injection
    - Implements OAuth2 with JWT for authentication
    - Follows REST API patterns
    - Provides clear error responses
    - Supports future RBAC expansion
"""

from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from Protexis_Command.api_internal.schemas.user import Token, UserCreate, UserResponse
from Protexis_Command.api_internal.security.jwt import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token,
    revoke_token,
)
from Protexis_Command.api_internal.security.oauth2 import get_current_active_user
from Protexis_Command.api_internal.security.password import get_password_hash, verify_password
from Protexis_Command.infrastructure.database.dependencies import get_db
from Protexis_Command.infrastructure.database.models.user import User, UserRole
from Protexis_Command.infrastructure.database.repositories.user_repository import UserRepository

router = APIRouter(tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserResponse:
    """Register a new user in the system.

    This endpoint handles new user registration with automatic role assignment.
    It performs email uniqueness validation and secure password hashing.

    Process Flow:
        1. Validates input data using UserCreate schema
        2. Checks for existing email to prevent duplicates
        3. Hashes password using bcrypt
        4. Assigns default USER role
        5. Creates user record in database
        6. Returns user information (excluding sensitive data)

    Related Components:
        - UserCreate schema: Validates registration input
        - UserResponse schema: Formats user response
        - UserRepository: Handles database operations
        - Password hashing: Secures user credentials

    Future RBAC Considerations:
        - Role assignment logic expansion
        - Custom role creation
        - Role hierarchy enforcement
        - Department/team-based role assignment

    Args:
        user_data: Validated user registration data (email, name, password)
        db: Async database session for transactions

    Returns:
        UserResponse: Created user information (excluding sensitive data)

    Raises:
        HTTPException:
            - 400: Email already registered
            - 500: Database operation failure
    """
    user_repo = UserRepository(db)

    # Check if user already exists
    if await user_repo.get_by_email(user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create user instance
    user = User(
        email=user_data.email,
        name=user_data.name,
        hashed_password=get_password_hash(user_data.password),
        role=UserRole.USER,
        is_active=True,
    )

    # Save user to database
    try:
        user = await user_repo.create(user)
        await db.commit()
        # Convert SQLAlchemy model to Pydantic model
        return UserResponse.model_validate(user)
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user",
        ) from e


@router.post("/login", response_model=Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Token:
    """Authenticate user and generate access token.

    This endpoint handles user authentication using OAuth2 password flow
    and generates JWT tokens for authenticated sessions.

    Process Flow:
        1. Validates login credentials
        2. Verifies user exists and is active
        3. Validates password using secure comparison
        4. Generates JWT access token
        5. Returns token with expiration info

    Related Components:
        - JWT token generation: Protexis_Command/api_protexis/security/jwt.py
        - Password verification: Protexis_Command/api_protexis/security/password.py
        - User repository: Database access for user verification
        - Token schema: Response formatting

    Future RBAC Considerations:
        - Role-based token claims
        - Permission-based access scopes
        - Role-specific token expiration
        - Multi-factor authentication integration

    Args:
        form_data: OAuth2 form containing username (email) and password
        db: Async database session for user lookup

    Returns:
        Token: JWT access token with expiration information

    Raises:
        HTTPException:
            - 401: Invalid credentials or inactive user
            - 500: Authentication process failure
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


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> UserResponse:
    """Get current user information.

    This endpoint returns the authenticated user's information.
    It requires a valid JWT token in the Authorization header.

    Args:
        current_user: Current authenticated user from token

    Returns:
        UserResponse: User information (excluding sensitive data)
    """
    return UserResponse.model_validate(current_user)


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    current_user: Annotated[User, Depends(get_current_active_user)],
    response: Response,
) -> dict:
    """Log out current user.

    This endpoint handles user logout by:
    1. Revoking the current JWT token
    2. Clearing any session data
    3. Returning success response

    Process Flow:
        1. Validate current user token
        2. Revoke token
        3. Clear session cookies
        4. Return success

    Args:
        current_user: Current authenticated user (from token)
        response: FastAPI response object for cookie manipulation

    Returns:
        dict: Success message
    """
    try:
        # Get token from current user context
        token = current_user.token if hasattr(current_user, "token") else None

        # Revoke token if present
        if token:
            await revoke_token(token)

        # Clear any session cookies
        response.delete_cookie(key="session")

        return {"message": "Successfully logged out"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed",
        ) from e
