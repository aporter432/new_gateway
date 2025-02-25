"""
Routes for authentication and authorization.

This module implements the authentication and authorization endpoints as defined in OGx-1.txt Section 3.
"""

from fastapi import APIRouter

from Protexis_Command.api.internal.routes.auth.user import router as user_router

# Create auth router with prefix
auth_router = APIRouter(prefix="/auth", tags=["Authentication"])

# Include user router
auth_router.include_router(user_router)
