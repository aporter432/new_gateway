from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from Protexis_Command.api_protexis.middleware.protexis_auth import add_protexis_auth_middleware
from Protexis_Command.api_protexis.routes import auth

app = FastAPI(
    title="Protexis API",
    description="Customer-facing API for device management and authentication",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

add_protexis_auth_middleware(app)

app.include_router(
    auth.router,
    prefix="/api",
    tags=["auth"],
)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
