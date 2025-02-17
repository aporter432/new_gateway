"""JWT token creation and validation.

This module implements JSON Web Token (JWT) handling for the gateway application,
providing secure token-based authentication and authorization.

Key Components:
    - Token Generation: Creates signed JWT tokens
    - Token Validation: Verifies token authenticity
    - Claim Management: Handles token payload data
    - Expiration Handling: Manages token lifecycle

Related Files:
    - src/api/routes/auth/user.py: Uses tokens for authentication
    - src/api/schemas/user.py: User data for token claims
    - src/core/app_settings.py: JWT configuration settings
    - src/api/security/password.py: Password verification for token generation

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

from core.app_settings import get_settings

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
        - Claim validation
        - Error handling

    Process Flow:
        1. Validate input data
        2. Add expiration claim
        3. Sign token with secret
        4. Return encoded token

    Args:
        data: Claims to include in token. Must contain either 'sub' or 'email'
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token string

    Raises:
        ValueError: If token data is None, empty, or missing required claims
    """
    if data is None or not data:
        raise ValueError("Token data cannot be None or empty")

    try:
        to_encode = data.copy()

        # Ensure we have both sub and email claims
        email = to_encode.get("email") or to_encode.get("sub")
        if not email:
            raise ValueError("Token data must contain either 'sub' or 'email' claim")

        to_encode.update({"email": email, "sub": email})  # Use email as subject if not provided

        expire = datetime.now(timezone.utc) + (
            expires_delta if expires_delta else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
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

    Security Checks:
        - Signature verification
        - Expiration validation
        - Structure validation
        - Claim presence
        - Algorithm verification

    Process Flow:
        1. Decode token
        2. Verify signature
        3. Validate expiration
        4. Extract claims
        5. Return token data

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
                detail="Token has been revoked",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Decode and verify token
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[ALGORITHM],
            options={"verify_exp": True},  # Explicitly verify expiration
        )

        # Extract claims
        email = payload.get("email")
        sub = payload.get("sub")
        exp = payload.get("exp")

        if not exp:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Create token data with optional claims
        token_data = TokenData(
            email=email or sub,  # Use sub as fallback for email
            exp=datetime.fromtimestamp(float(exp), tz=timezone.utc),
            sub=sub or email,  # Use email as fallback for sub
        )
        return token_data

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e
