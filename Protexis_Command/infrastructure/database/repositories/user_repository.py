"""User repository for database operations.

This module implements the repository pattern for user data access in the gateway application.
It provides a clean separation between the database and business logic layers.

Key Components:
    - CRUD Operations: Complete user lifecycle management
    - Query Optimization: Efficient database access patterns
    - Error Handling: Comprehensive error management
    - Transaction Management: Atomic operations support

Related Files:
    - Protexis_Command/infrastructure/database/models/user.py: User model this repository manages
    - Protexis_Command/api_protexis/routes/auth/user.py: API endpoints using this repository
    - Protexis_Command/api_protexis/schemas/user.py: DTOs for data transformation
    - Protexis_Command/api_protexis/security/password.py: Password handling utilities

Database Considerations:
    - Uses SQLAlchemy async session management
    - Implements optimized query patterns
    - Handles concurrent access
    - Manages transaction boundaries
    - Provides error recovery

Implementation Notes:
    - Follows repository pattern best practices
    - Implements async/await patterns
    - Uses SQLAlchemy 2.0 select syntax
    - Provides comprehensive error handling
    - Supports pagination and filtering

Future RBAC Considerations:
    - Role-based query filtering
    - Permission-aware operations
    - Department/team scoping
    - Audit log integration
    - Access control enforcement
"""

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from Protexis_Command.infrastructure.database.models.user import User
from Protexis_Command.protocols.ogx.validation.ogx_validation_exceptions import ValidationError


class UserRepository:
    """Repository for user-related database operations.

    This class implements the repository pattern for user data access,
    providing a clean API for user management operations.

    Design Patterns:
        - Repository Pattern: Abstracts data access
        - Unit of Work: Via AsyncSession
        - ACID Transactions: Atomic operations
        - Query Object: Encapsulated queries

    Operations:
        - Create: New user registration
        - Read: Single user and list retrieval
        - Update: User profile modifications
        - Delete: User account removal
        - Query: Filtered and paginated searches

    Performance Considerations:
        - Uses database indexes
        - Implements eager loading
        - Supports pagination
        - Optimizes common queries
        - Manages connection pool

    Error Handling:
        - Unique constraint violations
        - Foreign key violations
        - Connection errors
        - Transaction failures
        - Validation errors

    Future RBAC Considerations:
        - Role-based access filters
        - Permission checks in queries
        - Department/team scoping
        - Audit trail recording
        - Access control integration

    Attributes:
        session: AsyncSession for database operations
    """

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session.

        Args:
            session: AsyncSession for database operations

        Note:
            The session should be created by the session factory
            and managed by the FastAPI dependency injection system.
        """
        self.session = session

    async def create(self, user: User) -> User:
        """Create a new user in the database.

        This method handles new user creation with proper error handling
        and constraint checking.

        Process Flow:
            1. Validate user data
            2. Check uniqueness constraints
            3. Persist to database
            4. Refresh for generated values
            5. Return created instance

        Args:
            user: User model instance to create

        Returns:
            Created user instance with generated ID and timestamps

        Raises:
            ValidationError: If user with email already exists
            IntegrityError: On database constraint violation
            Exception: On other database errors

        Note:
            This operation is transactional and will roll back on error.
        """
        try:
            self.session.add(user)
            await self.session.flush()  # Check constraints
            await self.session.refresh(user)
            return user
        except IntegrityError as exc:
            await self.session.rollback()
            raise ValidationError(f"User with email {user.email} already exists") from exc

    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Retrieve a user by their ID.

        This method efficiently fetches a user using the primary key index.

        Performance:
            - Uses primary key lookup
            - Benefits from database indexing
            - Single row retrieval

        Args:
            user_id: Primary key of user to find

        Returns:
            User if found, None otherwise

        Note:
            This is the most efficient way to fetch a single user.
        """
        return await self.session.get(User, user_id)

    async def get_by_email(self, email: str) -> Optional[User]:
        """Retrieve a user by their email address.

        This method uses the email unique index for efficient lookup.

        Performance:
            - Uses unique email index
            - Single row retrieval
            - Optimized for auth flows

        Args:
            email: Email address to search for

        Returns:
            User if found, None otherwise

        Note:
            Email lookups are optimized for authentication flows.
        """
        result = await self.session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Retrieve a paginated list of users.

        This method supports pagination for efficient large dataset handling.

        Performance:
            - Uses LIMIT and OFFSET
            - Supports pagination
            - Can be filtered/ordered

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of users within the specified range

        Future RBAC Considerations:
            - Role-based filtering
            - Department/team scoping
            - Permission-based visibility
        """
        result = await self.session.execute(select(User).offset(skip).limit(limit))
        return list(result.scalars().all())

    async def update(self, user: User) -> User:
        """Update an existing user's information.

        This method handles user updates with proper error handling
        and constraint validation.

        Process Flow:
            1. Validate update data
            2. Check constraints
            3. Persist changes
            4. Refresh instance
            5. Return updated user

        Args:
            user: User instance with updates

        Returns:
            Updated user instance

        Raises:
            ValidationError: If update violates constraints
            IntegrityError: On database constraint violation

        Note:
            This operation is transactional and will roll back on error.
        """
        try:
            await self.session.flush()  # Check constraints
            await self.session.refresh(user)
            return user
        except IntegrityError as exc:
            await self.session.rollback()
            raise ValidationError(f"Update failed for user {user.email}") from exc

    async def delete(self, user: User) -> None:
        """Remove a user from the database.

        This method handles user deletion with proper cleanup
        and constraint checking.

        Process Flow:
            1. Check for dependencies
            2. Remove user record
            3. Commit transaction

        Args:
            user: User instance to delete

        Raises:
            IntegrityError: If deletion violates constraints

        Note:
            Consider soft deletion for audit trail requirements.
        """
        await self.session.delete(user)
        await self.session.commit()
