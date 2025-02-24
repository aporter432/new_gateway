"""Authentication models for the OGx API.

This module defines the request and response models for authentication endpoints
as specified in OGx-1.txt Section 4.1.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class TokenRequest(BaseModel):
    """Request model for obtaining an authentication token."""

    username: str = Field(..., description="OGx API username")
    password: str = Field(..., description="OGx API password")
    client_id: Optional[str] = Field(None, description="Optional client identifier")


class TokenResponse(BaseModel):
    """Response model containing the authentication token."""

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field("bearer", description="Token type, always 'bearer'")
    expires_at: datetime = Field(..., description="Token expiration timestamp")
    refresh_token: Optional[str] = Field(None, description="Optional refresh token")
