"""
Routes for authentication and authorization.

This module implements the authentication and authorization endpoints as defined in OGx-1.txt Section 3.
"""

from fastapi import APIRouter

from Protexis_Command.api.internal.routes.auth.roles import router as roles_router
from Protexis_Command.api.internal.routes.auth.user import router as user_router
from Protexis_Command.api.internal.routes.test_roles import router as test_roles_router

# Create auth router with prefix
auth_router = APIRouter(prefix="/auth", tags=["Authentication"])

# Include user router
auth_router.include_router(user_router)
auth_router.include_router(roles_router)
