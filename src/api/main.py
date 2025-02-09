"""Main FastAPI application.

This module provides:
- API route registration
- Middleware configuration
- Application startup/shutdown events
"""

from typing import Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.middleware.auth import add_auth_middleware
from api.routes import messages
from protocols.ogx.services.ogws_message_worker import get_message_worker

# Create FastAPI app
app = FastAPI(
    title="Smart Gateway API",
    description="API for OGWS message handling and device management",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add auth middleware
add_auth_middleware(app)

# Include routers
app.include_router(messages.router, prefix="/api/v1", tags=["messages"])


@app.on_event("startup")
async def startup_event() -> None:
    """Start background workers on application startup."""
    # Start message worker
    worker = await get_message_worker()
    app.state.message_worker = worker
    await worker.start()


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Stop background workers on application shutdown."""
    # Stop message worker
    if hasattr(app.state, "message_worker"):
        await app.state.message_worker.stop()


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/")
def read_root() -> Dict[str, str]:
    """Return a simple health check message."""
    return {"message": "Smart Gateway API is running!"}
