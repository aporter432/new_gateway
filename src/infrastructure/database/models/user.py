"""User model for authentication and authorization.

This module implements the user data model for the UI authentication system.
It follows the MVP requirements while maintaining extensibility for future enhancements.

Implementation Notes:
    - Uses SQLAlchemy for ORM
    - Follows existing database patterns
    - Implements minimal required fields
    - Ensures proper indexing for lookups
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class UserRole(str, Enum):
    """User role enumeration.

    Attributes:
        USER: Standard user with basic access
        ADMIN: Administrative user with full access
    """

    USER = "user"
    ADMIN = "admin"


class User(Base):
    """User model for authentication and authorization.

    This model implements the core user attributes required for MVP:
    - Email (used as username)
    - Name
    - Password (hashed)
    - Role
    - Active status
    - Timestamps

    Attributes:
        email: Unique email address used as username
        name: User's full name
        hashed_password: Bcrypt hashed password
        role: User role (user/admin)
        is_active: Whether the user account is active
        created_at: Timestamp of user creation
        updated_at: Timestamp of last update
    """

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(String(50), nullable=False, default=UserRole.USER)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, onupdate=datetime.utcnow
    )

    def __repr__(self) -> str:
        """Get string representation of the user.

        Returns:
            String representation with email and role
        """
        return f"User(email={self.email}, role={self.role})"
