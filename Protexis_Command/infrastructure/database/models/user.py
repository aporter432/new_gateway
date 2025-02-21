"""User model for authentication and authorization.

This module implements the core database model for user management in the gateway application.
It defines the user entity structure and relationships for SQLAlchemy ORM.

Key Components:
    - User Model: Core user entity with authentication fields
    - Role Enumeration: Basic role definition (expandable for RBAC)
    - Timestamps: Audit trail support
    - Indexes: Performance optimization for common queries

Related Files:
    - src/api/schemas/user.py: Pydantic schemas mapping to this model
    - src/infrastructure/database/repositories/user_repository.py: Repository layer for this model
    - src/api/routes/auth/user.py: API endpoints using this model
    - src/api/security/password.py: Password hashing for this model

Database Considerations:
    - Uses SQLAlchemy async ORM
    - Implements proper indexing for lookups
    - Ensures referential integrity
    - Supports audit trailing
    - Optimizes for read performance

Implementation Notes:
    - Follows SQLAlchemy 2.0 patterns
    - Uses typed ORM mappings
    - Implements proper cascade behaviors
    - Ensures proper constraint definitions
    - Supports async operations

Future RBAC Considerations:
    - Extended role hierarchy
    - Permission tables and relationships
    - Department/team associations
    - Access level tracking
    - Audit logging relationships
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import Boolean, DateTime
from sqlalchemy import Enum as SAEnum
from sqlalchemy import Index, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class UserRole(str, Enum):
    """User role enumeration for authorization control.

    This enumeration defines the basic role types in the system.
    It serves as the foundation for role-based access control.

    Attributes:
        USER: Standard user with basic access
        ADMIN: Administrative user with full access
    """

    USER = "user"
    ADMIN = "admin"

    def __str__(self) -> str:
        """Return the lowercase string value of the enum."""
        return self.value.lower()


class User(Base):
    """User model for authentication and authorization.

    This model defines the core user entity in the database, handling
    user authentication, authorization, and profile management.

    Table Structure:
        - __tablename__: 'users'
        - Primary Key: id (auto-incrementing)
        - Unique Constraints: email
        - Indexes: email, role
        - Timestamps: created_at, updated_at

    Attributes:
        id: Unique user identifier
        email: Email address (used as username)
        name: User's full name
        hashed_password: Bcrypt hashed password
        role: User's role (USER/ADMIN)
        is_active: Account status flag
        created_at: Account creation timestamp
        updated_at: Last modification timestamp

    Relationships:
        TBD based on future requirements:
        - User permissions
        - Department associations
        - Access logs
        - Session records

    Usage:
        - User authentication
        - Profile management
        - Authorization checks
        - Audit trailing

    Future RBAC Considerations:
        - Role relationship table
        - Permission associations
        - Department/team relationships
        - Access history tracking
        - Security log associations
    """

    __tablename__ = "users"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Authentication fields
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
        doc="User's email address (used as username)",
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Bcrypt hashed password",
    )

    # Profile fields
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="User's full name",
    )
    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole, name="userrole", values_callable=lambda x: [e.value.lower() for e in x]),
        default=UserRole.USER,
        nullable=False,
        index=True,
        doc="User's role for access control",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        doc="Whether the user account is active",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        doc="Timestamp of account creation",
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        onupdate=datetime.utcnow,
        doc="Timestamp of last update",
    )

    # Indexes
    __table_args__ = (
        Index("ix_users_email_role", "email", "role"),
    )  # Composite index for auth queries

    def __repr__(self) -> str:
        """Get string representation of the user.

        Returns:
            String representation with email and role
        """
        return f"User(email={self.email}, role={self.role})"
