"""Password hashing and verification utilities.

This module provides secure password handling:
- Password hashing with bcrypt
- Password verification
- Password validation rules
"""

from typing import Optional

import bcrypt
from passlib.context import CryptContext

# Configure password hashing
pwd_context = CryptContext(
    schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12  # Work factor for bcrypt
)


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt.

    Args:
        password: Plain text password to hash

    Returns:
        Hashed password string
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password to verify against

    Returns:
        True if password matches hash, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def validate_password(password: str) -> Optional[str]:
    """Validate password strength.

    Args:
        password: Password to validate

    Returns:
        Error message if password is invalid, None if valid

    Validation Rules:
        - Minimum 8 characters
        - Maximum 100 characters
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one number
        - At least one special character
    """
    if len(password) < 8:
        return "Password must be at least 8 characters long"
    if len(password) > 100:
        return "Password must be at most 100 characters long"
    if not any(c.isupper() for c in password):
        return "Password must contain at least one uppercase letter"
    if not any(c.islower() for c in password):
        return "Password must contain at least one lowercase letter"
    if not any(c.isdigit() for c in password):
        return "Password must contain at least one number"
    if not any(not c.isalnum() for c in password):
        return "Password must contain at least one special character"
    return None
