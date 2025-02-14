"""User repository for database operations.

This module implements the user repository pattern for database operations.
It provides:
- CRUD operations for users
- Password hashing
- Query optimization
- Error handling

Implementation Notes:
    - Uses SQLAlchemy for database operations
    - Implements repository pattern
    - Provides async operations
    - Handles common errors
"""

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.database.models.user import User
from protocols.ogx.validation.common.validation_exceptions import ValidationError


class UserRepository:
    """Repository for user-related database operations.

    This class implements the repository pattern for user operations:
    - Create user
    - Read user(s)
    - Update user
    - Delete user
    - Query optimization

    Attributes:
        session: AsyncSession for database operations
    """

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session.

        Args:
            session: AsyncSession for database operations
        """
        self.session = session

    async def create(self, user: User) -> User:
        """Create a new user.

        Args:
            user: User model instance to create

        Returns:
            Created user instance

        Raises:
            ValidationError: If user with email already exists
        """
        try:
            self.session.add(user)
            await self.session.commit()
            await self.session.refresh(user)
            return user
        except IntegrityError as exc:
            await self.session.rollback()
            raise ValidationError(f"User with email {user.email} already exists") from exc

    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID.

        Args:
            user_id: User ID to find

        Returns:
            User if found, None otherwise
        """
        return await self.session.get(User, user_id)

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email.

        Args:
            email: Email address to find

        Returns:
            User if found, None otherwise
        """
        result = await self.session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get all users with pagination.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of users
        """
        result = await self.session.execute(select(User).offset(skip).limit(limit))
        return list(result.scalars().all())

    async def update(self, user: User) -> User:
        """Update existing user.

        Args:
            user: User model instance with updates

        Returns:
            Updated user instance

        Raises:
            ValidationError: If update violates constraints
        """
        try:
            await self.session.commit()
            await self.session.refresh(user)
            return user
        except IntegrityError as exc:
            await self.session.rollback()
            raise ValidationError(f"Update failed for user {user.email}") from exc

    async def delete(self, user: User) -> None:
        """Delete user.

        Args:
            user: User model instance to delete
        """
        await self.session.delete(user)
        await self.session.commit()
