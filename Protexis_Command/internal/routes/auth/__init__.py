"""Authentication routes module.

This module provides authentication-related routes:
- User login
- Token validation
- Session management

Implementation Notes:
    - Uses FastAPI router
    - Implements JWT authentication
    - Follows REST API patterns
"""

from fastapi import APIRouter

from ....api.internal.routes.auth.user import router as user_router

# Create auth router with prefix
router = APIRouter(prefix="/auth")

# Include user routes
router.include_router(user_router)
