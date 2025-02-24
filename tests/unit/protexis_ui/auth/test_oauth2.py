"""Unit tests for OAuth2 implementation.

This module tests the OAuth2 password flow implementation, including:
- Current user extraction from token
- Active user validation
- Admin role verification
- Error handling for various scenarios
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from Protexis_Command.api_protexis.security.jwt import TokenData
from Protexis_Command.api_protexis.security.oauth2 import (
    get_current_active_user,
    get_current_admin_user,
    get_current_user,
)
from Protexis_Command.infrastructure.database.models.user import User, UserRole


@pytest.fixture
def mock_session():
    """Fixture for mocked database session."""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def mock_user():
    """Fixture for a mock user instance."""
    user = MagicMock(spec=User)
    user.email = "test@example.com"
    user.is_active = True
    user.role = UserRole.USER
    return user


@pytest.fixture
def mock_admin_user():
    """Fixture for a mock admin user instance."""
    user = MagicMock(spec=User)
    user.email = "admin@example.com"
    user.is_active = True
    user.role = UserRole.ADMIN
    return user


@pytest.fixture
def valid_token_data():
    """Fixture for valid token data."""
    return TokenData(
        email="test@example.com", exp=datetime.now(timezone.utc), sub="test@example.com"
    )


@pytest.mark.asyncio
async def test_get_current_user_success(mock_session, mock_user, valid_token_data):
    """Test successful current user extraction.

    Verifies:
    - Valid token is properly processed
    - User is correctly retrieved from database
    - User instance is returned
    """
    # Mock token verification
    with patch(
        "Protexis_Command.api_protexis.security.oauth2.verify_token", return_value=valid_token_data
    ):
        # Mock user repository
        with patch("Protexis_Command.api_protexis.security.oauth2.UserRepository") as mock_repo:
            mock_repo_instance = mock_repo.return_value
            mock_repo_instance.get_by_email = AsyncMock(return_value=mock_user)

            # Test the function
            user = await get_current_user("valid_token", mock_session)

            # Verify results
            assert user == mock_user
            mock_repo_instance.get_by_email.assert_called_once_with("test@example.com")


@pytest.mark.asyncio
async def test_get_current_user_invalid_token(mock_session):
    """Test handling of invalid token.

    Verifies:
    - Invalid token raises appropriate exception
    - Error details are correct
    """
    # Mock token verification to raise exception
    with patch(
        "Protexis_Command.api_protexis.security.oauth2.verify_token", side_effect=HTTPException(401)
    ):
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user("invalid_token", mock_session)

        assert exc_info.value.status_code == 401
        assert "Could not validate credentials" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_get_current_user_user_not_found(mock_session, valid_token_data):
    """Test handling of non-existent user.

    Verifies:
    - Non-existent user raises appropriate exception
    - Error details are correct
    """
    # Mock token verification
    with patch(
        "Protexis_Command.api_protexis.security.oauth2.verify_token", return_value=valid_token_data
    ):
        # Mock user repository with no user found
        with patch("Protexis_Command.api_protexis.security.oauth2.UserRepository") as mock_repo:
            mock_repo_instance = mock_repo.return_value
            mock_repo_instance.get_by_email.return_value = None

            with pytest.raises(HTTPException) as exc_info:
                await get_current_user("valid_token", mock_session)

            assert exc_info.value.status_code == 401
            assert "Could not validate credentials" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_get_current_active_user_success(mock_user):
    """Test successful active user validation.

    Verifies:
    - Active user is returned without modification
    """
    mock_user.is_active = True
    user = await get_current_active_user(mock_user)
    assert user == mock_user


@pytest.mark.asyncio
async def test_get_current_active_user_inactive(mock_user):
    """Test handling of inactive user.

    Verifies:
    - Inactive user raises appropriate exception
    - Error details are correct
    """
    mock_user.is_active = False
    with pytest.raises(HTTPException) as exc_info:
        await get_current_active_user(mock_user)

    assert exc_info.value.status_code == 400
    assert "Inactive user account" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_get_current_admin_user_success(mock_admin_user):
    """Test successful admin user validation.

    Verifies:
    - Admin user is returned without modification
    """
    user = await get_current_admin_user(mock_admin_user)
    assert user == mock_admin_user


@pytest.mark.asyncio
async def test_get_current_admin_user_not_admin(mock_user):
    """Test handling of non-admin user.

    Verifies:
    - Non-admin user raises appropriate exception
    - Error details are correct
    """
    with pytest.raises(HTTPException) as exc_info:
        await get_current_admin_user(mock_user)

    assert exc_info.value.status_code == 403
    assert "Administrative privileges required" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_get_current_user_missing_email(mock_session):
    """Test handling of token with missing email.

    Verifies:
    - Token with missing email raises appropriate exception
    - Error details are correct
    """
    # Create token data with missing email
    invalid_token_data = TokenData(
        email=None, exp=datetime.now(timezone.utc), sub="test@example.com"
    )

    # Mock token verification
    with patch(
        "Protexis_Command.api_protexis.security.oauth2.verify_token",
        return_value=invalid_token_data,
    ):
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user("valid_token", mock_session)

        assert exc_info.value.status_code == 401
        assert "Could not validate credentials" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_get_current_user_database_error(mock_session, valid_token_data):
    """Test handling of database errors.

    Verifies:
    - Database errors are caught and converted to auth errors
    - Error details are properly masked for security
    """
    with patch(
        "Protexis_Command.api_protexis.security.oauth2.verify_token", return_value=valid_token_data
    ):
        with patch("Protexis_Command.api_protexis.security.oauth2.UserRepository") as mock_repo:
            mock_repo_instance = mock_repo.return_value
            mock_repo_instance.get_by_email = AsyncMock(side_effect=Exception("DB Error"))

            with pytest.raises(HTTPException) as exc_info:
                await get_current_user("valid_token", mock_session)

            assert exc_info.value.status_code == 401
            assert "Could not validate credentials" in str(exc_info.value.detail)
            # Ensure DB error is not leaked
            assert "DB Error" not in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_get_current_active_user_none_user():
    """Test handling of None user input.

    Verifies:
    - None user input is handled gracefully
    - Appropriate error is raised
    """
    # Type ignore since we're testing None handling
    with pytest.raises(HTTPException) as exc_info:
        await get_current_active_user(None)  # type: ignore

    assert exc_info.value.status_code == 400
    assert "Invalid user" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_get_current_admin_user_none_user():
    """Test handling of None user input for admin check.

    Verifies:
    - None user input is handled gracefully
    - Appropriate error is raised
    """
    # Type ignore since we're testing None handling
    with pytest.raises(HTTPException) as exc_info:
        await get_current_admin_user(None)  # type: ignore

    assert exc_info.value.status_code == 400
    assert "Invalid user" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_get_current_admin_user_invalid_role(mock_user):
    """Test handling of invalid role value.

    Verifies:
    - Invalid role values are handled properly
    - Appropriate error is raised
    """
    # Set an invalid role value
    mock_user.role = "invalid_role"

    with pytest.raises(HTTPException) as exc_info:
        await get_current_admin_user(mock_user)

    assert exc_info.value.status_code == 403
    assert "Administrative privileges required" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_get_current_admin_user_missing_role(mock_user):
    """Test handling of user object missing role attribute.

    Verifies:
    - Missing role attribute is handled gracefully
    - Appropriate error is raised
    """
    # Remove role attribute
    delattr(mock_user, "role")

    with pytest.raises(HTTPException) as exc_info:
        await get_current_admin_user(mock_user)

    assert exc_info.value.status_code == 400
    assert "Invalid user role" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_get_current_user_malformed_token_data(mock_session):
    """Test handling of malformed token data.

    Verifies:
    - Malformed token data is handled gracefully
    - Appropriate error is raised
    """
    # Mock verify_token to raise HTTPException for malformed data
    with patch(
        "Protexis_Command.api_protexis.security.oauth2.verify_token",
        side_effect=HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials"
        ),
    ):
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user("malformed_token", mock_session)

        assert exc_info.value.status_code == 401
        assert "Could not validate credentials" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_get_current_active_user_missing_is_active(mock_user):
    """Test handling of user object missing is_active attribute.

    Verifies:
    - Missing is_active attribute is handled gracefully
    - Appropriate error is raised
    """
    # Remove is_active attribute
    delattr(mock_user, "is_active")

    with pytest.raises(HTTPException) as exc_info:
        await get_current_active_user(mock_user)

    assert exc_info.value.status_code == 400
    assert "Invalid user status" in str(exc_info.value.detail)
