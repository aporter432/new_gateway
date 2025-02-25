"""Main application entry point.

This module initializes and configures the FastAPI application.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from Protexis_Command.api.common.middleware.rate_limit import add_rate_limit_middleware
from Protexis_Command.api.common.middleware.validation import add_validation_middleware
from Protexis_Command.api.internal.routes.auth import user
from Protexis_Command.api.internal.routes.messages import router as protexis_router
from Protexis_Command.api.routes import auth, messages
from Protexis_Command.api.routes.api import router as ogx_router
from Protexis_Command.core.logging.log_settings import LoggingConfig
from Protexis_Command.core.logging.loggers import get_app_logger
from Protexis_Command.infrastructure.cache.redis import get_redis_url

# Initialize logging
config = LoggingConfig()
logger = get_app_logger(config)

# Create FastAPI app
app = FastAPI(
    title="OGx Gateway API",
    description="API for OGx message handling",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add rate limiting
redis_url = get_redis_url()
add_rate_limit_middleware(app, redis_url)

# Add validation
add_validation_middleware(app)

# Include routers
app.include_router(ogx_router)
app.include_router(protexis_router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# OGx API routes
app.include_router(auth.router, prefix="/api/v1.0", tags=["ogx-auth"])
app.include_router(messages.router, prefix="/api/v1", tags=["messages"])

# Protexis API routes
app.include_router(user.router, prefix="/api/auth", tags=["auth"])
