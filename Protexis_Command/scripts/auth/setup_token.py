"""Token setup script.

This script sets up authentication tokens for the application.
"""

import asyncio
import os
from typing import Optional

import httpx
from httpx import HTTPError
from infrastructure.redis import get_redis_client

from Protexis_Command.api_ogx.config import DEFAULT_TOKEN_EXPIRY
from Protexis_Command.api_ogx.services.auth.manager import OGxAuthManager
from Protexis_Command.api_ogx.validation.common.validation_exceptions import (
    OGxProtocolError,
    ValidationError,
)
from Protexis_Command.core.logging.loggers import get_auth_logger
from Protexis_Command.core.settings.app_settings import get_settings

# Remove unused imports:
# - json
# - datetime, timedelta, timezone
# - Dict


async def send_test_message(auth_header: dict, base_url: str, test_mobile_id: str) -> Optional[str]:
    """Send a test message to validate token with actual message flow.

    Returns message ID if successful, None if failed.
    """
    try:
        test_payload = {
            "DestinationID": test_mobile_id,
            "Payload": {"Name": "test_message", "SIN": 0, "MIN": 1, "Fields": []},  # System message
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{base_url}/submit/messages",
                headers={**auth_header, "Content-Type": "application/json"},
                json=test_payload,
            )
            response.raise_for_status()
            data = response.json()

            if data.get("ErrorID", 1) == 0 and data.get("Submissions"):
                return str(data["Submissions"][0].get("ID"))
            return None
    except (HTTPError, ValueError, KeyError) as e:
        logger = get_auth_logger("setup_token")
        logger.warning(
            "Test message validation failed",
            extra={
                "customer_id": get_settings().CUSTOMER_ID,
                "asset_id": "auth_service",
                "auth_info": {
                    "error_type": "validation",
                    "error_msg": str(e),
                    "service": "OGx",
                    "endpoint": "submit/messages",
                    "test_mobile_id": test_mobile_id,
                },
            },
        )
        return None


async def setup_initial_token() -> None:
    """Set up initial OGx auth token and store in Redis.

    This function:
    1. Initializes connection to Redis
    2. Creates an auth manager instance
    3. Acquires a new token from OGx
    4. Validates the token with test request
    5. Stores the token in Redis for reuse

    The token is required for all OGx API operations and is automatically
    refreshed by the auth manager before expiry.

    Raises:
        ValidationError: If token acquisition fails due to invalid credentials
        OGxProtocolError: If OGx protocol-level errors occur
        ConnectionError: If connection to OGx or Redis fails
        TimeoutError: If requests timeout
        IOError: If Redis operations fail
    """
    logger = get_auth_logger("setup_token")
    settings = get_settings()

    try:
        redis = await get_redis_client()
        auth_manager = OGxAuthManager(settings, redis)

        # Get token
        token = await auth_manager.get_valid_token()
        if not token:
            raise ValidationError("Failed to acquire token")

        # Validate token with service info
        auth_header = await auth_manager.get_auth_header()
        is_valid = await auth_manager.validate_token(auth_header)
        if not is_valid:
            raise ValidationError("Token validation failed with service info endpoint")

        # Optional: Send test message if test mobile ID configured
        test_message_id = None
        if hasattr(settings, "OGx_TEST_MOBILE_ID"):
            test_message_id = await send_test_message(
                auth_header, settings.OGx_BASE_URL, settings.OGx_TEST_MOBILE_ID
            )

        logger.info(
            "Token acquired, validated and stored",
            extra={
                "customer_id": settings.CUSTOMER_ID,  # Required context
                "asset_id": "auth_service",  # Required context
                "expiry": str(DEFAULT_TOKEN_EXPIRY),
                "auth_info": {
                    "token_acquired": True,
                    "token_validated": True,
                    "test_message_id": test_message_id,
                    "service": "OGx",
                },
            },
        )

    except ValidationError as e:
        logger.error(
            "Validation error during token setup: %s",
            str(e),
            extra={
                "customer_id": settings.CUSTOMER_ID,
                "asset_id": "auth_service",
                "auth_info": {"error_type": "validation", "error_msg": str(e), "service": "OGx"},
            },
        )
        os.exit(1)
    except OGxProtocolError as e:
        logger.error(
            "Protocol error during token setup: %s",
            str(e),
            extra={
                "customer_id": settings.CUSTOMER_ID,
                "asset_id": "auth_service",
                "auth_info": {"error_type": "protocol", "error_msg": str(e), "service": "OGx"},
            },
        )
        os.exit(1)
    except (ConnectionError, TimeoutError, IOError) as e:
        logger.error(
            "Connection/IO error during token setup: %s",
            str(e),
            exc_info=True,
            extra={
                "customer_id": settings.CUSTOMER_ID,
                "asset_id": "auth_service",
                "auth_info": {"error_type": "connection", "error_msg": str(e), "service": "OGx"},
            },
        )
        os.exit(1)


if __name__ == "__main__":
    asyncio.run(setup_initial_token())
