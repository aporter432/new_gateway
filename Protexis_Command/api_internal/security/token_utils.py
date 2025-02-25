"""Token validation utilities.

This module provides basic token validation functions.
It's kept separate from the main JWT handling to avoid circular dependencies.
"""

import re


def verify_token_format(token: str) -> bool:
    """Verify that a token has valid JWT format.

    This is a basic format check only - not a cryptographic verification.
    Full verification happens in the auth routes.

    Args:
        token: Token string to verify

    Returns:
        bool: True if token has valid format, False otherwise
    """
    # Basic JWT format: header.payload.signature
    jwt_pattern = r"^[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+$"
    return bool(re.match(jwt_pattern, token))
