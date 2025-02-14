"""User schemas for request/response validation.

This module implements Pydantic models for user-related API operations.
It provides:
- Request validation
- Response serialization
- Data transformation

Implementation Notes:
    - Uses Pydantic for validation
    - Follows API schema patterns
    - Implements field-level validation
    - Provides clear error messages
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    """Base user schema with shared attributes.

    This model contains fields common to all user operations.
    """

    email: EmailStr = Field(..., description="User's email address")
    name: str = Field(..., min_length=1, max_length=255, description="User's full name")


class UserCreate(UserBase):
    """Schema for user creation requests.

    This model extends UserBase with password field for registration.
    Password will be hashed before storage.
    """

    password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="User's password (will be hashed)",
    )


class UserUpdate(BaseModel):
    """Schema for user update requests.

    This model allows updating user fields individually.
    All fields are optional.
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
    """Schema for user information from database.

    This model represents the user as stored in the database,
    including system fields but excluding sensitive data.
    """

    id: int
    is_active: bool
    role: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class UserResponse(UserInDB):
    """Schema for user information in API responses.

    This model represents the user data returned in API responses.
    It excludes sensitive information and includes computed fields.
    """

    # Currently identical to UserInDB, but allows for future response-specific customization


class Token(BaseModel):
    """Schema for authentication tokens.

    This model represents the token response structure
    for successful authentication.
    """

    access_token: str
    token_type: str = "bearer"
    expires_in: int  # Seconds until token expires
