"""JWT token creation and validation.

This module provides JWT token handling:
- Token creation with claims
- Token validation and verification
- Token payload extraction
"""

from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from fastapi import HTTPException, status
from jose import JWTError, jwt
from pydantic import BaseModel

from core.app_settings import get_settings

# JWT configuration
settings = get_settings()
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # 30 minutes


class TokenData(BaseModel):
    """Token payload data."""

    email: str
    exp: datetime
    sub: str


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a new JWT access token.

    Args:
        data: Data to encode in token
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token string

    Raises:
        ValueError: If token creation fails
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta if expires_delta else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    try:
        encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    except JWTError as e:
        raise ValueError(f"Failed to create access token: {str(e)}")


def verify_token(token: str) -> TokenData:
    """Verify and decode a JWT token.

    Args:
        token: JWT token to verify

    Returns:
        TokenData containing decoded payload

    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        token_data = TokenData(
            email=email,
            exp=datetime.fromtimestamp(payload.get("exp")),
            sub=payload.get("sub"),
        )
        return token_data
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
