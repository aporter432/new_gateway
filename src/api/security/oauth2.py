"""OAuth2 password flow implementation.

This module implements the OAuth2 password flow authentication for the gateway application,
providing secure user authentication and authorization dependencies.

Key Components:
    - OAuth2 Password Flow: Standard authentication scheme
    - User Dependencies: Current user injection
    - Role-based Access: User role verification
    - Active Status Check: User status validation

Related Files:
    - src/api/security/jwt.py: JWT token handling
    - src/api/middleware/ogws_auth.py: Authentication middleware
    - src/api/routes/auth/user.py: Authentication endpoints
    - src/infrastructure/database/models/user.py: User model

Security Considerations:
    - Implements OAuth2 password flow
    - Uses JWT for token-based auth
    - Validates user status
    - Enforces role-based access
    - Provides secure dependency injection

Implementation Notes:
    - Uses FastAPI's dependency injection
    - Implements bearer token auth
    - Provides role-based guards
    - Handles token validation
    - Manages user session state

Future RBAC Considerations:
    - Permission-based access control
    - Role hierarchy support
    - Custom authorization rules
    - Scope-based access
    - Department/team authorization
"""

from typing import Optional, Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from api.security.jwt import TokenData, verify_token
from infrastructure.database.dependencies import get_db
from infrastructure.database.models import User
from infrastructure.database.repositories.user_repository import UserRepository

# OAuth2 scheme configuration with token URL
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="auth/login",  # URL for token acquisition
    scheme_name="JWT",  # Name in OpenAPI docs
    description="JWT token authentication",  # OpenAPI description
)


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """Get the current authenticated user from the token.

    This dependency verifies the JWT token and retrieves the corresponding user.
    It serves as the base authentication dependency for protected endpoints.

    Security Flow:
        1. Extract token from request
        2. Verify token signature and expiration
        3. Extract user identifier
        4. Retrieve user from database
        5. Return authenticated user

    Dependencies:
        - oauth2_scheme: Extracts JWT from request
        - get_db: Provides database session

    Args:
        token: JWT token from request header
        session: Database session for user lookup

    Returns:
        Authenticated User instance

    Raises:
        HTTPException:
            - 401: Invalid or expired token
            - 401: User not found
            - 401: Missing or invalid claims

    Usage:
        ```python
        @router.get("/me")
        async def read_me(user: User = Depends(get_current_user)):
            return user
        ```
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Verify token and extract claims
        token_data: TokenData = verify_token(token)

        # Validate required claims
        if token_data.email is None:
            raise credentials_exception

        # Retrieve user from database
        user_repo = UserRepository(session)
        user = await user_repo.get_by_email(token_data.email)
        if user is None:
            raise credentials_exception

        return user

    except Exception:
        raise credentials_exception


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Get the current user and verify active status.

    This dependency builds on get_current_user to ensure the user is active.
    It should be used for endpoints that require an active user account.

    Security Checks:
        - Valid authentication (via get_current_user)
        - Active account status
        - Valid user session

    Args:
        current_user: User from get_current_user dependency

    Returns:
        Verified active User instance

    Raises:
        HTTPException: 400 if user account is inactive

    Usage:
        ```python
        @router.post("/update")
        async def update_me(
            user: User = Depends(get_current_active_user)
        ):
            return user
        ```

    Future RBAC Considerations:
        - Account status levels
        - Session validation
        - Access restrictions
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account",
        )
    return current_user


async def get_current_admin_user(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> User:
    """Get the current user and verify admin role.

    This dependency ensures the user is both active and has admin privileges.
    It should be used for endpoints that require administrative access.

    Security Checks:
        - Valid authentication (via get_current_user)
        - Active account status (via get_current_active_user)
        - Admin role verification
        - Administrative privileges

    Args:
        current_user: User from get_current_active_user dependency

    Returns:
        Verified admin User instance

    Raises:
        HTTPException: 403 if user is not an admin

    Usage:
        ```python
        @router.delete("/users/{user_id}")
        async def delete_user(
            user_id: int,
            admin: User = Depends(get_current_admin_user)
        ):
            return {"deleted": user_id}
        ```

    Future RBAC Considerations:
        - Role hierarchy
        - Permission-based access
        - Administrative scope levels
        - Delegated administration
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative privileges required",
        )
    return current_user
