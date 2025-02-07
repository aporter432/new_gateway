"""
This script is used to setup the initial token for the application.

Uses the OGWS auth flow defined in OGWS-1.txt section 4.1.1.
"""

import asyncio
import sys

from core.config import get_settings
from core.security import OGWSAuthManager
from infrastructure.redis import get_redis_client
from protocols.ogx.constants import DEFAULT_TOKEN_EXPIRY
from protocols.ogx.exceptions import ValidationError, OGxProtocolError


async def setup_initial_token() -> None:
    """Set up initial OGWS auth token and store in Redis."""
    try:
        settings = get_settings()
        redis = await get_redis_client()
        auth_manager = OGWSAuthManager(settings, redis)

        token = await auth_manager.get_valid_token()
        if not token:
            raise ValidationError("Failed to acquire token")

        print(f"Token acquired and stored. Expires: {DEFAULT_TOKEN_EXPIRY}")

    except ValidationError as e:
        print(f"Validation error: {e}", file=sys.stderr)
        sys.exit(1)
    except OGxProtocolError as e:
        print(f"Protocol error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(setup_initial_token())
