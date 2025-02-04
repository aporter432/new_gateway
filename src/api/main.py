"""
This module contains the main FastAPI application.
It includes the endpoints for the messages API.
"""

from fastapi import FastAPI

from .routes.messages import router as messages_router

app = FastAPI(title="Smart Gateway API")

# Include message-related endpoints
app.include_router(messages_router, prefix="/api")


@app.get("/")
def read_root():
    return {"message": "Smart Gateway API is running!"}
