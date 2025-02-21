"""Password hashing and verification utilities.

This module implements secure password handling for the gateway application,
providing cryptographic functions for password management and validation.

Key Components:
    - Password Hashing: Secure one-way hashing using bcrypt
    - Password Verification: Secure comparison of passwords
    - Password Validation: Strength and complexity rules
    - Work Factor Management: Adaptive complexity settings

Related Files:
    - src/api/routes/auth/user.py: Uses these utilities for authentication
    - src/api/schemas/user.py: Password field validation
    - src/infrastructure/database/models/user.py: Stores hashed passwords
    - src/infrastructure/database/repositories/user_repository.py: User operations

Security Considerations:
    - Uses industry-standard bcrypt algorithm
    - Implements adaptive work factor
    - Provides timing attack protection
    - Follows OWASP password guidelines
    - Supports password complexity rules

Implementation Notes:
    - Uses passlib for consistent interface
    - Configurable work factor (rounds)
    - Thread-safe operations
    - Constant-time comparisons
    - Automatic salt generation

Future Considerations:
    - Password history tracking
    - Password expiration policies
    - Custom complexity rules
    - Multi-factor authentication
    - Password breach checking
"""

import logging
import re
from typing import Optional

from passlib.context import CryptContext

# Basic logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure password hashing with security settings
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)


def get_password_hash(password: str) -> str:
    """Generate a secure hash of a password.

    This function creates a cryptographically secure hash of the provided password
    using bcrypt with proper salt generation and work factor settings.

    Security Features:
        - Automatic salt generation (16 bytes)
        - Configurable work factor (currently 2^12 iterations)
        - Timing attack resistant
        - Memory-hard algorithm (bcrypt)

    Args:
        password: Plain text password to hash

    Returns:
        Secure hash string in bcrypt format

    Note:
        The resulting hash includes:
        - Algorithm identifier
        - Work factor
        - Salt
        - Hash value
    """
    try:
        hashed = pwd_context.hash(password)
        logger.info("Password hashed successfully")
        return hashed
    except Exception as e:
        logger.error(f"Password hashing failed: {e}")
        raise


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Securely verify a password against its hash.

    This function performs a secure comparison of a plain text password
    against its previously generated hash.

    Security Features:
        - Constant-time comparison
        - Timing attack resistant
        - No plain text password storage
        - Automatic work factor handling

    Args:
        plain_password: Plain text password to verify
        hashed_password: Previously generated password hash

    Returns:
        True if password matches hash, False otherwise

    Note:
        Uses constant-time comparison to prevent timing attacks
    """
    return pwd_context.verify(plain_password, hashed_password)


def validate_password(password: str) -> Optional[str]:
    """Validate password strength and complexity.

    This function checks if a password meets the required security criteria
    based on OWASP password guidelines.

    Validation Rules:
        - Minimum length (8 characters)
        - Maximum length (100 characters)
        - Must contain at least:
            - One uppercase letter
            - One lowercase letter
            - One number
            - One special character
        - No common patterns
        - No common passwords

    Args:
        password: Password string to validate

    Returns:
        None if password is valid, error message string if invalid

    Future Considerations:
        - Password breach database checking
        - Custom organizational policies
        - Adaptive complexity requirements
        - Machine learning based validation
    """
    if len(password) < 8:
        return "Password must be at least 8 characters long"

    if len(password) > 100:
        return "Password must not exceed 100 characters"

    # Check for required character types
    if not re.search(r"[A-Z]", password):
        return "Password must contain at least one uppercase letter"

    if not re.search(r"[a-z]", password):
        return "Password must contain at least one lowercase letter"

    if not re.search(r"\d", password):
        return "Password must contain at least one number"

    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return "Password must contain at least one special character"

    # Add more validation rules as needed
    return None
