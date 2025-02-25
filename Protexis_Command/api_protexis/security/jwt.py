"""JWT token creation and validation.

This module implements JSON Web Token (JWT) handling for the gateway application,
providing secure token-based authentication and authorization.

Key Components:
    - Token Generation: Creates signed JWT tokens
    - Token Validation: Verifies token authenticity
    - Claim Management: Handles token payload data
    - Expiration Handling: Manages token lifecycle

Related Files:
    - Protexis_Command/api_protexis/routes/auth/user.py: Uses tokens for authentication
    - Protexis_Command/api_protexis/schemas/user.py: User data for token claims
    - Protexis_Command/core/app_settings.py: JWT configuration settings
    - Protexis_Command/api_protexis/security/password.py: Password verification for token generation

Security Considerations:
    - Uses industry-standard JWT implementation
    - Implements secure signing algorithms
    - Enforces token expiration
    - Validates token structure
    - Protects against common JWT attacks

Implementation Notes:
    - Uses python-jose for JWT operations
    - Configurable signing algorithm
    - Automatic expiration handling
    - Claim validation
    - Error handling

Future Considerations:
    - Token refresh mechanism
    - Blacklist/revocation support
    - Role-based claims
    - Custom claim validation
    - Token rotation policies
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from fastapi import HTTPException, status
from jose import JWTError, jwt
from pydantic import BaseModel, Field

from Protexis_Command.core.settings.app_settings import get_settings

# JWT configuration from settings
settings = get_settings()
ALGORITHM = settings.JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # 60 minutes default expiration

# Store for revoked tokens
# In production, use Redis or database
REVOKED_TOKENS = set()


class TokenData(BaseModel):
    """Token payload data structure.

    This model defines the structure and validation rules for JWT claims.
    It ensures consistent token payload formatting and validation.

    Attributes:
        email: User's email for identification
        exp: Token expiration timestamp
        sub: Subject claim (typically user ID)

    Usage:
        - Token payload validation
        - Claim extraction
        - Authorization checks

    Future RBAC Considerations:
        - Role claims
        - Permission claims
        - Department/team claims
        - Access scope claims
    """

    email: Optional[str] = Field(None, description="User's email address")
    exp: datetime = Field(..., description="Token expiration timestamp")
    sub: Optional[str] = Field(None, description="Subject identifier")


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a new JWT access token.

    This function generates a secure JWT token with the provided claims
    and configurable expiration time.

    Security Features:
        - Secure signing algorithm
        - Automatic expiration
        - Error handling

    Process Flow:
        1. Validate input data
        2. Add expiration claim
        3. Sign token with secret
        4. Return encoded token

    Args:
        data: Claims to include in token
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token string

    Raises:
        ValueError: If token data is None or empty
        ValueError: If token data does not contain required claims
    """
    if not data:
        raise ValueError("Token data cannot be None or empty")

    # Validate that the token contains either 'sub' or 'email' claim
    if "sub" not in data and "email" not in data:
        raise ValueError("Token data must contain either 'sub' or 'email' claim")

    try:
        to_encode = data.copy()

        # Add expiration as Unix timestamp
        expire = datetime.now(timezone.utc) + (
            expires_delta if expires_delta else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        to_encode.update({"exp": int(expire.timestamp())})

        # Create token with positional arguments
        try:
            encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, ALGORITHM)
            return encoded_jwt
        except (TypeError, ValueError) as e:
            raise ValueError("Failed to create access token: Data is not JSON serializable") from e
    except ValueError:
        raise
    except Exception as e:
        raise ValueError(f"Failed to create access token: {str(e)}") from e


async def revoke_token(token: str) -> None:
    """Revoke a JWT token.

    In production, this should:
    1. Store token in Redis/database blacklist
    2. Set expiry matching token expiry
    3. Clean up expired tokens periodically

    Args:
        token: JWT token to revoke
    """
    REVOKED_TOKENS.add(token)


def verify_token(token: str) -> TokenData:
    """Verify and decode a JWT token.

    This function validates the token's signature, expiration,
    and structure, returning the decoded payload if valid.

    Args:
        token: JWT token string to verify

    Returns:
        TokenData containing validated claims

    Raises:
        HTTPException:
            - 401: Invalid or expired token
            - 403: Invalid token structure
    """
    try:
        # Check if token is revoked
        if token in REVOKED_TOKENS:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Decode and verify token
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[ALGORITHM],
                options={"verify_exp": True},
            )
        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            ) from e

        # Extract claims
        email = payload.get("email")
        sub = payload.get("sub")
        exp = payload.get("exp")

        # Validate required claims
        if not exp:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Convert exp to datetime
        exp_datetime = datetime.fromtimestamp(float(exp), tz=timezone.utc)

        # Validate and normalize claims
        email_val = str(email).strip() if email else None
        sub_val = str(sub).strip() if sub else None

        # If either claim is an empty string after stripping, reject the token
        if (email is not None and not email_val) or (sub is not None and not sub_val):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Copy sub to email if email is missing
        if not email_val and sub_val:
            email_val = sub_val
        # Copy email to sub if sub is missing
        elif not sub_val and email_val:
            sub_val = email_val

        # Create token data - allow None values for both email and sub
        token_data = TokenData(email=email_val, sub=sub_val, exp=exp_datetime)

        # Validate that at least one of email or sub is present
        if not email_val and not sub_val:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return token_data

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e
