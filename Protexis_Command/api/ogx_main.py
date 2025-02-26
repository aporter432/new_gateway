"""OGx API main application module.

This module initializes and configures the FastAPI application for the OGx Gateway.
It sets up middleware, routes, and background workers for message handling.
"""

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

# Third-party imports
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from Protexis_Command.api.common.middleware.ogx_auth import add_ogx_auth_middleware
from Protexis_Command.api.protocols.ogx.routes.messages import router as messages_router
from Protexis_Command.api.protocols.ogx.routes.terminal import router as terminal_router
from Protexis_Command.api.protocols.ogx.routes.updates import router as updates_router
from Protexis_Command.api.protocols.ogx.services.ogx_message_worker import get_message_worker

# First-party imports
from Protexis_Command.core.logging.loggers import get_protocol_logger

logger = get_protocol_logger()


async def initialize_worker() -> None:
    """Initialize and start the message worker.

    This function creates a new message worker instance and starts it.
    Any startup errors are logged but not re-raised to prevent application
    startup failure.
    """
    try:
        worker = await get_message_worker()
        app.state.message_worker = worker
        await worker.start()
        logger.info("Message worker started successfully")
    except (ConnectionError, TimeoutError) as e:
        logger.error(f"Failed to connect to message worker: {str(e)}")
        app.state.worker_error = str(e)
    except ValueError as e:
        logger.error(f"Invalid configuration for message worker: {str(e)}")
        app.state.worker_error = str(e)
    except Exception as e:  # pylint: disable=broad-except
        # We catch all exceptions here to prevent app startup failure
        # but log them for debugging
        logger.error(f"Unexpected error starting message worker: {str(e)}")
        app.state.worker_error = str(e)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application lifespan.

    This context manager handles startup and shutdown tasks:
    - On startup: Initializes the message worker
    - On shutdown: Gracefully stops the message worker

    Args:
        app: The FastAPI application instance
    """
    worker_task = asyncio.create_task(initialize_worker())
    logger.info("Application startup complete")
    yield
    if worker_task:
        await worker_task
    if hasattr(app.state, "message_worker"):
        await app.state.message_worker.stop()


app = FastAPI(
    title="OGx API",
    description="Internal API for OGx message handling and protocol management",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

add_ogx_auth_middleware(app)

app.include_router(
    messages_router,
    prefix="/api/v1",
    tags=["messages"],
)

app.include_router(
    terminal_router,
    prefix="/api/v1",
    tags=["terminal-operations"],
)

app.include_router(
    updates_router,
    prefix="/api/v1",
    tags=["terminal-updates"],
)


@app.get("/health")
async def health_check() -> dict:
    """Check application health status.

    Returns:
        dict: Health check response with status
    """
    return {"status": "healthy"}
