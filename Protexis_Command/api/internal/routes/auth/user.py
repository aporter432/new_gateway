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

from datetime import datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from Protexis_Command.api.common.auth.jwt import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token,
    revoke_token,
)
from Protexis_Command.api.common.auth.oauth2 import get_current_active_user, get_current_admin_user
from Protexis_Command.api.common.auth.password import (
    generate_secure_password,
    get_password_hash,
    validate_password,
    verify_password,
)
from Protexis_Command.api.common.auth.role_hierarchy import RoleHierarchy
from Protexis_Command.api.common.email import get_email_service
from Protexis_Command.api.internal.schemas.user import (
    Token,
    UserCreate,
    UserCreateWithGeneratedPassword,
    UserCreationResponse,
    UserResponse,
)
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
        4. Checks if temporary password has expired (24-hour limit)
        5. Generates JWT access token
        6. Returns token with expiration info

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
            - 403: Temporary password expired
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

    # Check if temporary password has expired (older than 24 hours)
    if user.password_is_temporary:
        password_age = datetime.utcnow() - user.password_created_at
        if password_age.total_seconds() > 24 * 60 * 60:  # 24 hours in seconds
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your temporary password has expired. Please contact technical support for a password reset.",
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


@router.post("/admin/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    role: UserRole,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Create a new user with specified role (admin only).

    This endpoint allows administrators to create users with specific roles,
    enforcing role hierarchy constraints to prevent privilege escalation.

    Args:
        user_data: User creation data (email, name, password)
        role: Role to assign to the new user
        current_user: The admin making the request
        db: Database session

    Returns:
        Created user information (excluding sensitive data)

    Raises:
        HTTPException:
            - 400: Email already registered
            - 403: Insufficient permissions to assign the requested role
            - 500: Database operation failure
    """
    user_repo = UserRepository(db)

    # Check if user already exists
    if await user_repo.get_by_email(user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Check if the admin has permission to assign this role
    if not RoleHierarchy.can_manage_role(str(current_user.role), str(role)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot assign a role with higher permissions than your own",
        )

    # Create user instance with the specified role
    user = User(
        email=user_data.email,
        name=user_data.name,
        hashed_password=get_password_hash(user_data.password),
        role=role,
        is_active=True,
    )

    # Save user to database
    try:
        user = await user_repo.create(user)
        await db.commit()
        return UserResponse.model_validate(user)
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user",
        ) from e


@router.post(
    "/admin/users/with-generated-password",
    response_model=UserCreationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_user_with_generated_password(
    user_data: UserCreateWithGeneratedPassword,
    role: UserRole,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> UserCreationResponse:
    """Create a new user with auto-generated password (admin only).

    This endpoint allows administrators to create users with specific roles and
    system-generated passwords. The password is generated securely, sent to the
    user via email, and returned in the response.

    Process Flow:
        1. Validates input data and admin permissions
        2. Checks for existing email to prevent duplicates
        3. Generates a secure random password
        4. Creates the user with the provided role
        5. Sends welcome email with credentials
        6. Returns user information with the generated password

    Args:
        user_data: User creation data (email, name)
        role: Role to assign to the new user
        current_user: The admin making the request
        db: Database session

    Returns:
        Created user information including the generated password

    Raises:
        HTTPException:
            - 400: Email already registered
            - 403: Insufficient permissions to assign the requested role
            - 500: Database operation failure or email sending failure
    """
    user_repo = UserRepository(db)
    email_service = get_email_service()

    # Check if user already exists
    if await user_repo.get_by_email(user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Check if the admin has permission to assign this role
    if not RoleHierarchy.can_manage_role(str(current_user.role), str(role)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot assign a role with higher permissions than your own",
        )

    # Generate a secure random password
    generated_password = generate_secure_password()

    # Create user instance with the specified role
    user = User(
        email=user_data.email,
        name=user_data.name,
        hashed_password=get_password_hash(generated_password),
        role=role,
        is_active=True,
        password_created_at=datetime.utcnow(),  # Set the password creation time
        password_is_temporary=True,  # Mark as temporary password that needs to be changed
    )

    # Save user to database
    try:
        user = await user_repo.create(user)
        await db.commit()

        # Send welcome email with credentials
        email_subject = "Welcome to Protexis System - Your Account Information"
        email_body = f"""
        Hello {user.name},

        Welcome to the Protexis System!

        An account has been created for you with the following credentials:

        Email: {user.email}
        Password: {generated_password}
        Role: {user.role}

        IMPORTANT: This is a temporary password that will expire in 24 hours.
        Please log in at https://protexis.example.com/login and change your password immediately.

        If you do not change your password within 24 hours, you will need to contact technical support
        to have your password reset.

        This password was automatically generated and should be kept confidential.

        Best regards,
        The Protexis Team
        """

        # Send email asynchronously
        email_sent = await email_service.send_email(
            recipient=user.email, subject=email_subject, body=email_body
        )

        if not email_sent:
            # If email fails, log it but don't fail the request
            # The password is still returned in the response
            print(f"Warning: Failed to send password email to {user.email}")

        # Return user with the generated password
        user_response = UserCreationResponse.model_validate(user)
        user_response.generated_password = generated_password
        return user_response

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}",
        ) from e


@router.post("/change-password", response_model=UserResponse)
async def change_password(
    current_password: str,
    new_password: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserResponse:
    """Change user password.

    This endpoint allows users to change their password, including temporary passwords.
    It verifies the current password before setting the new password.

    Process Flow:
        1. Verifies current password
        2. Validates new password strength
        3. Updates password in database
        4. Clears temporary password status if applicable
        5. Returns updated user information

    Args:
        current_password: User's current password for verification
        new_password: New password to set
        current_user: Current authenticated user (from token)
        db: Database session

    Returns:
        Updated user information

    Raises:
        HTTPException:
            - 400: Invalid current password or weak new password
            - 500: Database operation failure
    """
    # Verify current password
    if not verify_password(current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    # Validate new password strength
    password_error = validate_password(new_password)
    if password_error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=password_error,
        )

    # Update user with new password
    user_repo = UserRepository(db)
    try:
        current_user.hashed_password = get_password_hash(new_password)
        current_user.password_created_at = datetime.utcnow()
        current_user.password_is_temporary = False  # Mark as permanent password

        await user_repo.update(current_user)
        await db.commit()

        return UserResponse.model_validate(current_user)
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update password",
        ) from e


@router.post(
    "/admin/users/{user_id}/reset-password",
    response_model=UserCreationResponse,
    status_code=status.HTTP_200_OK,
)
async def reset_user_password(
    user_id: int,
    current_user: Annotated[User, Depends(get_current_admin_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserCreationResponse:
    """Reset a user's password (admin only).

    This endpoint allows administrators to reset a user's password,
    generating a new temporary password that will be emailed to the user.
    Useful when users forget passwords or temporary passwords expire.

    Process Flow:
        1. Verifies admin permissions
        2. Retrieves target user
        3. Generates new temporary password
        4. Updates user in database
        5. Sends email with new credentials
        6. Returns user information with new password

    Args:
        user_id: ID of the user to reset password for
        current_user: The admin making the request
        db: Database session

    Returns:
        User information with the new generated password

    Raises:
        HTTPException:
            - 404: User not found
            - 403: Insufficient permissions based on role hierarchy
            - 500: Database operation or email sending failure
    """
    user_repo = UserRepository(db)
    email_service = get_email_service()

    # Get the user whose password needs to be reset
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Check if the admin has permission to manage this user's role
    if not RoleHierarchy.can_manage_role(str(current_user.role), str(user.role)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to reset this user's password",
        )

    # Generate a new secure temporary password
    generated_password = generate_secure_password()

    try:
        # Update user with new password
        user.hashed_password = get_password_hash(generated_password)
        user.password_created_at = datetime.utcnow()
        user.password_is_temporary = True

        await user_repo.update(user)
        await db.commit()

        # Send email with new credentials
        email_subject = "Protexis System - Your Password Has Been Reset"
        email_body = f"""
        Hello {user.name},

        Your password for the Protexis System has been reset by an administrator.

        Your new temporary password is: {generated_password}

        Please log in at https://protexis.example.com/login and change your password immediately.
        This temporary password will expire in 24 hours.

        If you did not request this password reset, please contact your system administrator.

        Best regards,
        The Protexis Team
        """

        # Send email asynchronously
        email_sent = await email_service.send_email(
            recipient=user.email, subject=email_subject, body=email_body
        )

        if not email_sent:
            # If email fails, log it but don't fail the request
            # The password is still returned in the response
            print(f"Warning: Failed to send password reset email to {user.email}")

        # Return user with the generated password
        user_response = UserCreationResponse.model_validate(user)
        user_response.generated_password = generated_password
        return user_response

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset password: {str(e)}",
        ) from e
