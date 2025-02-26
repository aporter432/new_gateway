"""Validation middleware for the OGx API.

This module implements request/response validation as specified in OGx-1.txt.
It ensures all data conforms to the protocol specification before processing.
"""

from typing import Callable, Dict, Type

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from Protexis_Command.api.protocols.ogx.models.messages import (
    MessageRequest,
    MultiDestinationRequest,
)
from Protexis_Command.protocols.ogx.validation.ogx_validation_exceptions import (
    MessageValidationError,
)
from Protexis_Command.protocols.ogx.validation.ogx_validation_exceptions import (
    ValidationError as OGxValidationError,
)


class ValidationMiddleware(BaseHTTPMiddleware):
    """Middleware for validating requests and responses."""

    def __init__(self, app: ASGIApp):
        """Initialize validation middleware.

        Args:
            app: The ASGI application
        """
        super().__init__(app)
        self.validators: Dict[str, Type[BaseModel]] = {
            "/api/v1.0/submit/messages": MessageRequest,
            "/api/v1.0/submit/to_multiple": MultiDestinationRequest,
        }

    async def validate_request(self, request: Request) -> None:
        """Validate incoming request data.

        Args:
            request: The incoming request

        Raises:
            ValidationError: If request data is invalid
            MessageValidationError: If message format is invalid
        """
        path = request.url.path
        if path not in self.validators:
            return

        try:
            body = await request.json()
            validator = self.validators[path]
            validator.model_validate(body)
        except ValidationError as e:
            raise MessageValidationError(str(e))

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request through validation.

        Args:
            request: The incoming request
            call_next: Next middleware in chain

        Returns:
            Response: The HTTP response
        """
        try:
            if request.method in ("POST", "PUT", "PATCH"):
                await self.validate_request(request)
            response = await call_next(request)
            return response
        except (ValidationError, OGxValidationError) as e:
            return JSONResponse(
                status_code=422,
                content={"detail": str(e)},
            )
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={"detail": f"Validation error: {str(e)}"},
            )


def add_validation_middleware(app: FastAPI) -> None:
    """Register validation middleware with FastAPI app.

    Args:
        app: The FastAPI application
    """
    app.add_middleware(ValidationMiddleware)
