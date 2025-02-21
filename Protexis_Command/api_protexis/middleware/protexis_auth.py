from typing import Callable

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from ..security.jwt import verify_token  # You'll need to implement this


class ProtexisAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            # Verify JWT token for Protexis API
            auth_header = request.headers.get("Authorization")
            if not auth_header:
                return JSONResponse(
                    status_code=401, content={"detail": "No authentication token provided"}
                )

            token = auth_header.split(" ")[1]
            if not await verify_token(token):
                return JSONResponse(
                    status_code=401, content={"detail": "Invalid authentication token"}
                )

            return await call_next(request)

        except Exception as e:
            return JSONResponse(
                status_code=500, content={"detail": "Protexis API error", "error": str(e)}
            )


def add_protexis_auth_middleware(app: FastAPI) -> None:
    app.add_middleware(ProtexisAuthMiddleware)
