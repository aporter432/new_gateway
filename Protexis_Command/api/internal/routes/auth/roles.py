from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from Protexis_Command.api.common.auth.oauth2 import get_current_admin_user
from Protexis_Command.api.common.auth.role_descriptions import RoleDescriptions
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

    # Update user role
    user.role = role
    await user_repo.update(user)
    await db.commit()

    return UserResponse.model_validate(user)
