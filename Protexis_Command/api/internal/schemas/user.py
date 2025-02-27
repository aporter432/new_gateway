"""User schemas for request/response validation.

This module implements Pydantic models for user-related API operations in the gateway application.
It defines the data structures for user management, authentication, and authorization.

Key Components:
    - User Base Schema: Common user attributes
    - Registration Schema: New user creation with validation
    - Update Schema: User profile modifications
    - Response Schema: API response formatting
    - Token Schema: Authentication token structure

Related Files:
    - Protexis_Command/api_protexis/routes/auth/user.py: Authentication endpoints using these schemas
    - Protexis_Command/infrastructure/database/models/user.py: SQLAlchemy models these schemas map to
    - Protexis_Command/api_protexis/security/jwt.py: JWT token handling using Token schema
    - Protexis_Command/api_protexis/security/password.py: Password handling for UserCreate/Update schemas

Implementation Notes:
    - Uses Pydantic for validation and serialization
    - Implements strict field validation rules
    - Separates concerns between request/response models
    - Supports SQLAlchemy model mapping
    - Provides clear validation error messages

Future RBAC Considerations:
    - Role-specific schema fields
    - Permission set representations
    - Department/team affiliations
    - Custom role attributes
    - Audit trail metadata
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    """Base user schema with shared attributes.

    This model defines the core user fields used across different operations.
    It enforces basic validation rules and field constraints.

    Attributes:
        email: Unique email address for user identification
        name: User's full name with length constraints

    Usage:
        - Base class for UserCreate and UserResponse
        - Ensures consistent user attribute validation
        - Maintains single source of truth for shared fields
    """

    email: EmailStr = Field(..., description="User's email address")
    name: str = Field(..., min_length=1, max_length=255, description="User's full name")


class UserCreate(UserBase):
    """Schema for user registration requests.

    This model extends UserBase to include password field and registration-specific validation.
    It handles new user creation while enforcing security requirements.

    Attributes:
        email: Inherited from UserBase
        name: Inherited from UserBase
        password: Raw password (will be hashed before storage)

    Usage:
        - Validates registration requests
        - Enforces password requirements
        - Maps to User database model

    Security Notes:
        - Password is never stored in raw form
        - Minimum password length enforced
        - Password complexity rules applied
    """

    password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="User's password (will be hashed)",
    )


class UserCreateWithGeneratedPassword(UserBase):
    """Schema for admin user creation with generated password.

    This model extends UserBase but doesn't require a password field,
    as the system will generate a secure random password and send it to the user.

    Attributes:
        email: Inherited from UserBase
        name: Inherited from UserBase

    Usage:
        - Admin user creation
        - System-generated secure passwords
        - Email notification of credentials

    Security Notes:
        - Generated password follows security policy
        - Password is emailed to user directly
        - User prompted to change on first login
    """

    role: Optional[str] = Field(None, description="User's role in the system (if specified)")


class UserUpdate(BaseModel):
    """Schema for user profile updates.

    This model defines fields that can be modified after user creation.
    All fields are optional to support partial updates.

    Attributes:
        name: Optional update to user's name
        email: Optional update to email address
        password: Optional password change
        is_active: Optional account status update

    Usage:
        - Partial user profile updates
        - Account status management
        - Password changes
        - Email address updates

    Future RBAC Considerations:
        - Role modification fields
        - Permission updates
        - Department changes
        - Access level modifications
    """

    name: Optional[str] = Field(None, min_length=1, max_length=255, description="User's full name")
    email: Optional[EmailStr] = Field(None, description="User's email address")
    password: Optional[str] = Field(
        None,
        min_length=8,
        max_length=100,
        description="User's new password (will be hashed)",
    )
    is_active: Optional[bool] = Field(None, description="Whether the user is active")


class UserInDB(UserBase):
    """Internal schema for database user representation.

    This model represents the user as stored in the database, including
    system-managed fields but excluding sensitive data like passwords.

    Attributes:
        id: Unique user identifier
        is_active: Account status flag
        role: User's role in the system
        created_at: Account creation timestamp
        updated_at: Last modification timestamp

    Usage:
        - Database record mapping
        - Internal user representation
        - Audit trail support

    Future RBAC Considerations:
        - Extended role information
        - Permission sets
        - Access history
        - Security clearance levels
    """

    id: int
    is_active: bool
    role: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class UserResponse(UserInDB):
    """Schema for user information in API responses.

    This model defines the user data structure returned by API endpoints.
    It inherits from UserInDB but can be extended with computed fields
    and excludes sensitive information.

    Usage:
        - API response formatting
        - Public user profile representation
        - User list endpoints

    Future RBAC Considerations:
        - Role-specific data inclusion
        - Permission summaries
        - Access level indicators
        - Team/department information
    """


class UserCreationResponse(UserResponse):
    """Schema for user creation response with password information.

    This model extends UserResponse to include the generated password.
    It is used only when returning information about a newly created user
    with a system-generated password.

    Attributes:
        generated_password: The plain text generated password (only returned once)

    Usage:
        - Admin user creation responses
        - System-generated password feedback
        - For API consumption only (not database storage)
    """

    generated_password: Optional[str] = Field(
        None, description="Generated password (only included in creation response)"
    )


class Token(BaseModel):
    """Schema for authentication token responses.

    This model defines the structure of authentication tokens returned
    after successful login or token refresh operations.

    Attributes:
        access_token: JWT token string
        token_type: Token type (always "bearer")
        expires_in: Token lifetime in seconds

    Usage:
        - Login response formatting
        - Token refresh responses
        - OAuth2 compliance

    Future RBAC Considerations:
        - Role-based token metadata
        - Permission claims
        - Access scope information
        - Token refresh rules
    """

    access_token: str
    token_type: str = "bearer"
    expires_in: int  # Seconds until token expires
