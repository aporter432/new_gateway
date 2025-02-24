"""Protexis API main application.

This module initializes the FastAPI application and configures middleware and routes.
"""

from Protexis_Command.api_protexis.app_init import create_app, init_routes

app = create_app()
init_routes(app)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
