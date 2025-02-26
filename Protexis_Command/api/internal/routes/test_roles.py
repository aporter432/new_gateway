from fastapi import APIRouter, Depends

from Protexis_Command.api.common.auth.roles import requires_roles
from Protexis_Command.infrastructure.database.models.user import User, UserRole

router = APIRouter(tags=["test"])


@router.get("/api/test/user")
async def test_user_role(user: User = Depends(requires_roles(UserRole.USER))):
    """Test endpoint for any user."""
    return {"message": "You have user role access", "email": user.email, "role": user.role}


@router.get("/api/test/admin")
async def test_admin_role(user: User = Depends(requires_roles(UserRole.ADMIN))):
    """Test endpoint for admin only."""
    return {"message": "You have admin role access", "email": user.email, "role": user.role}
