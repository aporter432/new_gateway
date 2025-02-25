"""Application initialization module.

This module handles the initialization of the FastAPI application,
including middleware and route configuration.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application instance
    """
    app = FastAPI(
        title="Protexis API",
        description="Customer-facing API for device management and authentication",
        version="1.0.0",
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3001"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Health check endpoint
    @app.get("/health")
    async def health_check():
        return {"status": "healthy"}

    return app


def init_routes(app: FastAPI) -> None:
    """Initialize application routes.

    Args:
        app: FastAPI application instance
    """
    from Protexis_Command.api_internal.routes import auth

    app.include_router(
        auth.router,
        prefix="/api",
        tags=["auth"],
    )
