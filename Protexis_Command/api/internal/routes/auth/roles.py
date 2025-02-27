from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from Protexis_Command.api.common.auth.oauth2 import get_current_active_user, get_current_admin_user
from Protexis_Command.api.common.auth.role_descriptions import RoleDescriptions
from Protexis_Command.api.common.auth.role_hierarchy import RoleHierarchy
from Protexis_Command.api.internal.schemas.user import UserResponse
from Protexis_Command.infrastructure.database.dependencies import get_db
from Protexis_Command.infrastructure.database.models.user import User, UserRole
from Protexis_Command.infrastructure.database.repositories.user_repository import UserRepository

router = APIRouter(prefix="/roles", tags=["roles"])


@router.get("/", response_model=List[dict])
async def get_all_roles():
    """Get all available roles with descriptions."""
    return RoleDescriptions.get_all_roles_with_descriptions()


@router.put("/{user_id}", response_model=UserResponse)
async def update_user_role(
    user_id: int,
    role: UserRole,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a user's role (admin only)."""
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Check if the current user has permission to assign this role
    if not RoleHierarchy.can_manage_role(str(current_user.role), str(role)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot assign a role with higher permissions than your own",
        )

    # Update user role
    user.role = role
    await user_repo.update(user)
    await db.commit()

    return UserResponse.model_validate(user)


@router.get("/can-assign/{role}", response_model=dict)
async def can_assign_role(
    role: UserRole,
    current_user: User = Depends(get_current_active_user),
):
    """Check if the current user can assign the specified role.

    This endpoint validates if the current user has sufficient permissions
    to assign or manage users with the specified role, based on the role
    hierarchy defined in the system.

    Args:
        role: The role to check permission for
        current_user: The current authenticated user

    Returns:
        Dictionary with 'can_assign' boolean and explanation
    """
    can_assign = RoleHierarchy.can_manage_role(str(current_user.role), str(role))

    return {
        "can_assign": can_assign,
        "role": str(role),
        "current_user_role": str(current_user.role),
        "message": (
            "You can assign this role"
            if can_assign
            else "You cannot assign a role with higher permissions than your own"
        ),
    }
