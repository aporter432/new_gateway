from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from Protexis_Command.api.common.auth.RBA.roles import requires_roles
from Protexis_Command.infrastructure.database.models.user import User, UserRole


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


@pytest.mark.asyncio
async def test_requires_roles_with_single_role(mock_user):
    """Test requires_roles with a single allowed role."""
    # Create the dependency with USER role
    role_checker = requires_roles(UserRole.USER)

    # Mock the get_current_active_user dependency
    get_current_active_user_mock = AsyncMock(return_value=mock_user)

    # Test the role checker
    result = await role_checker(current_user=await get_current_active_user_mock())
    assert result == mock_user


@pytest.mark.asyncio
async def test_requires_roles_with_multiple_roles(mock_admin_user):
    """Test requires_roles with multiple allowed roles."""
    # Create the dependency with multiple roles
    allowed_roles = [UserRole.ADMIN, UserRole.PROTEXIS_ADMINISTRATOR]
    role_checker = requires_roles(allowed_roles)

    # Mock the get_current_active_user dependency
    get_current_active_user_mock = AsyncMock(return_value=mock_admin_user)

    # Test the role checker
    result = await role_checker(current_user=await get_current_active_user_mock())
    assert result == mock_admin_user


@pytest.mark.asyncio
async def test_requires_roles_with_insufficient_permissions(mock_user):
    """Test requires_roles with insufficient permissions."""
    # Create the dependency requiring ADMIN role
    role_checker = requires_roles(UserRole.ADMIN)

    # Mock the get_current_active_user dependency
    get_current_active_user_mock = AsyncMock(return_value=mock_user)

    # Test that it raises HTTPException for insufficient permissions
    with pytest.raises(HTTPException) as exc_info:
        await role_checker(current_user=await get_current_active_user_mock())

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Insufficient permissions"


@pytest.mark.asyncio
async def test_requires_roles_with_list_insufficient_permissions(mock_user):
    """Test requires_roles with insufficient permissions using a list of roles."""
    # Create the dependency requiring admin roles
    allowed_roles = [UserRole.ADMIN, UserRole.PROTEXIS_ADMINISTRATOR]
    role_checker = requires_roles(allowed_roles)

    # Mock the get_current_active_user dependency
    get_current_active_user_mock = AsyncMock(return_value=mock_user)

    # Test that it raises HTTPException for insufficient permissions
    with pytest.raises(HTTPException) as exc_info:
        await role_checker(current_user=await get_current_active_user_mock())

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Insufficient permissions"


@pytest.mark.asyncio
async def test_requires_roles_with_protexis_roles(mock_user):
    """Test requires_roles with Protexis-specific roles."""
    # Modify mock user to have a Protexis role
    mock_user.role = UserRole.PROTEXIS_VIEW

    # Create the dependency with Protexis roles
    allowed_roles = [UserRole.PROTEXIS_VIEW, UserRole.PROTEXIS_REQUEST_READ]
    role_checker = requires_roles(allowed_roles)

    # Mock the get_current_active_user dependency
    get_current_active_user_mock = AsyncMock(return_value=mock_user)

    # Test the role checker
    result = await role_checker(current_user=await get_current_active_user_mock())
    assert result == mock_user
    assert result.role == UserRole.PROTEXIS_VIEW
