from fastapi import APIRouter, Depends

from Protexis_Command.api.common.auth.roles import requires_roles
from Protexis_Command.infrastructure.database.models.user import User, UserRole

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/admin")
async def admin_dashboard(
    user: User = Depends(requires_roles([UserRole.ADMIN, UserRole.PROTEXIS_ADMIN]))
):
    """Dashboard for admins only."""
    return {"message": "Welcome to the admin dashboard"}


@router.get("/tech-configs")
async def tech_configurations(user: User = Depends(requires_roles(UserRole.PROTEXIS_TECH_ADMIN))):
    """Technical configurations for tech admins only."""
    return {"message": "Technical configuration settings"}
