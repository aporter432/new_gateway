"""Unit tests for UserRepository.

This module tests the UserRepository class, which handles database operations for users.
Tests focus on isolated functionality without actual database connections.
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from Protexis_Command.infrastructure.database.models.user import User, UserRole
from Protexis_Command.infrastructure.database.repositories.user_repository import UserRepository
from Protexis_Command.protocol.ogx.validation.ogx_validation_exceptions import ValidationError


@pytest.fixture
def mock_session():
    """Fixture for mocked database session."""
    session = AsyncMock(spec=AsyncSession)
    session.flush = AsyncMock()
    session.refresh = AsyncMock()
    session.rollback = AsyncMock()
    session.execute = AsyncMock()
    return session


@pytest.fixture
def mock_user():
    """Fixture for a mock user instance."""
    user = MagicMock(spec=User)
    user.id = 1
    user.email = "test@example.com"
    user.name = "Test User"
    user.role = UserRole.USER
    user.is_active = True
    user.created_at = datetime.utcnow()
    user.updated_at = None
    return user


@pytest.mark.asyncio
async def test_create_user_success(mock_session, mock_user):
    """Test successful user creation.

    Verifies:
    - User is added to session
    - Constraints are checked
    - User is refreshed
    - Created user is returned
    """
    repo = UserRepository(mock_session)
    result = await repo.create(mock_user)

    # Verify interactions
    mock_session.add.assert_called_once_with(mock_user)
    mock_session.flush.assert_called_once()
    mock_session.refresh.assert_called_once_with(mock_user)
    assert result == mock_user


@pytest.mark.asyncio
async def test_create_user_duplicate_email(mock_session, mock_user):
    """Test handling of duplicate email during creation.

    Verifies:
    - IntegrityError is caught
    - Session is rolled back
    - ValidationError is raised with correct message
    """
    # Mock flush to raise IntegrityError
    mock_session.flush.side_effect = IntegrityError(
        "Duplicate email", params=None, orig=Exception("Duplicate key")
    )

    repo = UserRepository(mock_session)
    with pytest.raises(ValidationError) as exc_info:
        await repo.create(mock_user)

    assert f"User with email {mock_user.email} already exists" in str(exc_info.value)
    mock_session.rollback.assert_called_once()


@pytest.mark.asyncio
async def test_get_by_id_found(mock_session, mock_user):
    """Test successful user retrieval by ID.

    Verifies:
    - Correct method is used for ID lookup
    - Found user is returned
    """
    mock_session.get.return_value = mock_user

    repo = UserRepository(mock_session)
    result = await repo.get_by_id(1)

    mock_session.get.assert_called_once_with(User, 1)
    assert result == mock_user


@pytest.mark.asyncio
async def test_get_by_id_not_found(mock_session):
    """Test user retrieval by ID when user doesn't exist.

    Verifies:
    - Correct method is used for ID lookup
    - None is returned when user is not found
    """
    mock_session.get.return_value = None

    repo = UserRepository(mock_session)
    result = await repo.get_by_id(999)

    mock_session.get.assert_called_once_with(User, 999)
    assert result is None


@pytest.mark.asyncio
async def test_get_by_email_found(mock_session, mock_user):
    """Test successful user retrieval by email.

    Verifies:
    - Correct query is executed
    - Found user is returned
    """
    # Mock execute result
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_user
    mock_session.execute = AsyncMock(return_value=mock_result)

    repo = UserRepository(mock_session)
    result = await repo.get_by_email("test@example.com")

    assert result == mock_user
    assert mock_session.execute.call_count == 1
    # Verify query includes email filter
    call_args = mock_session.execute.call_args[0][0]
    assert str(call_args).find("email") != -1


@pytest.mark.asyncio
async def test_get_by_email_not_found(mock_session):
    """Test user retrieval by email when user doesn't exist.

    Verifies:
    - Correct query is executed
    - None is returned when user is not found
    """
    # Mock execute result with no user found
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute = AsyncMock(return_value=mock_result)

    repo = UserRepository(mock_session)
    result = await repo.get_by_email("nonexistent@example.com")

    assert result is None
    assert mock_session.execute.call_count == 1


@pytest.mark.asyncio
async def test_get_all_with_pagination(mock_session, mock_user):
    """Test retrieval of paginated user list.

    Verifies:
    - Correct query is executed with pagination
    - List of users is returned
    - Pagination parameters are applied
    """
    # Mock execute result
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [mock_user]
    mock_result = MagicMock()
    mock_result.scalars.return_value = mock_scalars
    mock_session.execute = AsyncMock(return_value=mock_result)

    repo = UserRepository(mock_session)
    result = await repo.get_all(skip=10, limit=20)

    assert result == [mock_user]
    assert mock_session.execute.call_count == 1
    # Verify query includes pagination
    call_args = mock_session.execute.call_args[0][0]
    assert str(call_args).find("LIMIT") != -1
    assert str(call_args).find("OFFSET") != -1


@pytest.mark.asyncio
async def test_update_user_success(mock_session, mock_user):
    """Test successful user update.

    Verifies:
    - Constraints are checked
    - User is refreshed
    - Updated user is returned
    """
    repo = UserRepository(mock_session)
    result = await repo.update(mock_user)

    mock_session.flush.assert_called_once()
    mock_session.refresh.assert_called_once_with(mock_user)
    assert result == mock_user


@pytest.mark.asyncio
async def test_update_user_constraint_violation(mock_session, mock_user):
    """Test handling of constraint violation during update.

    Verifies:
    - IntegrityError is caught
    - Session is rolled back
    - ValidationError is raised with correct message
    """
    # Mock flush to raise IntegrityError
    mock_session.flush.side_effect = IntegrityError(
        "Constraint violation", params=None, orig=Exception("Unique constraint failed")
    )

    repo = UserRepository(mock_session)
    with pytest.raises(ValidationError) as exc_info:
        await repo.update(mock_user)

    assert f"Update failed for user {mock_user.email}" in str(exc_info.value)
    mock_session.rollback.assert_called_once()


@pytest.mark.asyncio
async def test_delete_user(mock_session, mock_user):
    """Test user deletion.

    Verifies:
    - User is deleted from session
    - Changes are committed
    """
    repo = UserRepository(mock_session)
    await repo.delete(mock_user)

    mock_session.delete.assert_called_once_with(mock_user)
    mock_session.commit.assert_called_once()
