from typing import List, Union

from fastapi import Depends, HTTPException, status

from Protexis_Command.api.common.auth.oauth2 import get_current_active_user
from Protexis_Command.infrastructure.database.models.user import User, UserRole


def requires_roles(allowed_roles: Union[UserRole, List[UserRole]]):
    """
    Dependency to check if user has one of the required roles.

    Args:
        allowed_roles: A single role or list of roles allowed to access the endpoint

    Returns:
        A dependency function that validates the user's role
    """
    if isinstance(allowed_roles, UserRole):
        allowed_roles = [allowed_roles]

    async def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user

    return role_checker
