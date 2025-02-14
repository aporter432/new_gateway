"""JWT token creation and validation.

This module provides JWT token handling:
- Token creation with claims
- Token validation and verification
- Token payload extraction
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from fastapi import HTTPException, status
from jose import JWTError, jwt
from pydantic import BaseModel

from core.app_settings import get_settings

# JWT configuration
settings = get_settings()
ALGORITHM = settings.JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # 30 minutes


class TokenData(BaseModel):
    """Token payload data."""

    email: Optional[str] = None
    exp: datetime
    sub: Optional[str] = None


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
    try:
        to_encode = data.copy()
        expire = datetime.utcnow() + (
            expires_delta if expires_delta else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    except (JWTError, TypeError) as e:  # Also catch TypeError for JSON serialization errors
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
        # Verify and decode the token
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[ALGORITHM],
            options={"verify_exp": False, "require_exp": True},  # We'll verify exp manually
        )

        exp_timestamp = payload.get("exp")

        # Validate expiration claim
        if exp_timestamp is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Convert timestamps to UTC for comparison
        exp_datetime = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
        current_time = datetime.now(tz=timezone.utc)

        if exp_datetime <= current_time:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",  # Keep consistent error message
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Create token data without validation
        token_data = TokenData(
            email=payload.get("sub"),
            exp=exp_datetime,
            sub=payload.get("sub"),
        )
        return token_data

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
