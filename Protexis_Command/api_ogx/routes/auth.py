"""Authentication routes for OGx API.

This module implements the authentication endpoints for the OGx API:
- Token acquisition
- Token validation
- Token refresh
"""

from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, status
from pydantic import BaseModel

from Protexis_Command.api_ogx.services.auth.manager import OGxAuthManager, get_auth_manager
from Protexis_Command.protocol.ogx.validation.common.validation_exceptions import (
    AuthenticationError,
    OGxProtocolError,
    RateLimitError,
    ValidationError,
)


class TokenResponse(BaseModel):
    """Token response model matching OGWS spec."""

    token_type: str = "bearer"  # Lowercase as per spec
    expires_in: int
    access_token: str


router = APIRouter(tags=["auth"])


@router.post("/api/v1.0/auth/token", response_model=TokenResponse)
async def get_token(
    grant_type: str = Form(..., description="Must be set to client_credentials"),
    expires_in: Optional[int] = Form(None, description="Token expiry time in seconds"),
    auth_manager: OGxAuthManager = Depends(get_auth_manager),
) -> TokenResponse:
    """Get access token using client credentials flow.

    Args:
        grant_type: Must be "client_credentials"
        expires_in: Optional token expiry time in seconds
        auth_manager: Injected auth manager instance

    Returns:
        TokenResponse with access token

    Raises:
        HTTPException:
            - 400: Invalid grant type
            - 401: Invalid credentials
            - 429: Rate limit exceeded
            - 500: Internal server error
    """
    if grant_type != "client_credentials":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="grant_type must be client_credentials",
        )

    try:
        token = await auth_manager.get_valid_token()
        return TokenResponse(
            access_token=token,
            expires_in=expires_in or 604800,  # Default to 7 days if not specified
        )

    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        ) from e

    except RateLimitError as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(e),
            headers={"Retry-After": "60"},  # Default 60 second retry
        ) from e

    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    except OGxProtocolError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from e
