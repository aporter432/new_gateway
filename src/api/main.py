"""Main FastAPI application.

This module provides:
- API route registration
- Middleware configuration
- Application startup/shutdown events
"""

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Dict, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.middleware.auth import add_auth_middleware
from api.routes import messages
from core.logging.loggers import get_protocol_logger
from protocols.ogx.services.ogws_message_worker import get_message_worker

# Get logger
logger = get_protocol_logger()

# Background task for worker initialization
worker_task: Optional[asyncio.Task] = None


async def initialize_worker() -> None:
    """Initialize message worker in background."""
    try:
        # Start message worker
        worker = await get_message_worker()
        app.state.message_worker = worker
        await worker.start()
        logger.info("Message worker started successfully")
    except Exception as e:
        # Log error but don't prevent app from starting
        logger.error(f"Failed to start message worker: {str(e)}")
        # Store error in app state for health checks
        app.state.worker_error = str(e)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan context manager for FastAPI application."""
    # Startup
    global worker_task
    worker_task = asyncio.create_task(initialize_worker())
    logger.info("Application startup complete")
    yield
    # Shutdown
    try:
        # Wait for worker initialization to complete
        if worker_task:
            try:
                await worker_task
            except Exception as e:
                logger.error(f"Worker initialization failed during shutdown: {str(e)}")

        # Stop message worker
        if hasattr(app.state, "message_worker"):
            await app.state.message_worker.stop()
            logger.info("Message worker stopped successfully")
    except Exception as e:
        logger.error(f"Error stopping message worker: {str(e)}")


# Create FastAPI app
app = FastAPI(
    title="Smart Gateway API",
    description="API for OGWS message handling and device management",
    version="1.0.0",
    lifespan=lifespan,
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


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    # Return healthy even if worker failed to start
    # This allows the container to start and retry connecting to Redis
    return {"status": "healthy"}


@app.get("/")
def read_root() -> Dict[str, str]:
    """Return a simple health check message."""
    return {"message": "Smart Gateway API is running!"}
