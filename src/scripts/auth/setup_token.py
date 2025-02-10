"""Setup initial authentication token for the gateway application.

This script handles the initial authentication token setup required for the gateway
to communicate with OGWS (OGx Gateway Web Service). It:
- Retrieves settings from environment/configuration
- Connects to Redis for token storage
- Acquires a new token using OGWS auth flow
- Validates token with test request
- Stores the token in Redis for reuse

The token is required for all subsequent API calls to OGWS. Token expiry and
refresh is handled automatically by the auth manager.

Usage:
    python -m scripts.auth.setup_token

References:
    OGWS-1.txt section 4.1.1 - Authentication Flow

Raises:
    ValidationError: If token acquisition fails due to invalid credentials
    OGxProtocolError: If OGWS protocol-level errors occur
    ConnectionError: If connection to OGWS or Redis fails
    TimeoutError: If requests timeout
    IOError: If Redis operations fail
"""

import asyncio
import sys
from typing import Optional

import httpx
from httpx import HTTPError

from core.app_settings import get_settings
from core.logging.loggers import get_auth_logger
from core.security import OGWSAuthManager
from infrastructure.redis import get_redis_client
from protocols.ogx.constants import DEFAULT_TOKEN_EXPIRY
from protocols.ogx.validation.common.exceptions import OGxProtocolError, ValidationError


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
                    "service": "OGWS",
                    "endpoint": "submit/messages",
                    "test_mobile_id": test_mobile_id,
                },
            },
        )
        return None


async def setup_initial_token() -> None:
    """Set up initial OGWS auth token and store in Redis.

    This function:
    1. Initializes connection to Redis
    2. Creates an auth manager instance
    3. Acquires a new token from OGWS
    4. Validates the token with test request
    5. Stores the token in Redis for reuse

    The token is required for all OGWS API operations and is automatically
    refreshed by the auth manager before expiry.

    Raises:
        ValidationError: If token acquisition fails due to invalid credentials
        OGxProtocolError: If OGWS protocol-level errors occur
        ConnectionError: If connection to OGWS or Redis fails
        TimeoutError: If requests timeout
        IOError: If Redis operations fail
    """
    logger = get_auth_logger("setup_token")
    settings = get_settings()

    try:
        redis = await get_redis_client()
        auth_manager = OGWSAuthManager(settings, redis)

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
        if hasattr(settings, "OGWS_TEST_MOBILE_ID"):
            test_message_id = await send_test_message(
                auth_header, settings.OGWS_BASE_URL, settings.OGWS_TEST_MOBILE_ID
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
                    "service": "OGWS",
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
                "auth_info": {"error_type": "validation", "error_msg": str(e), "service": "OGWS"},
            },
        )
        sys.exit(1)
    except OGxProtocolError as e:
        logger.error(
            "Protocol error during token setup: %s",
            str(e),
            extra={
                "customer_id": settings.CUSTOMER_ID,
                "asset_id": "auth_service",
                "auth_info": {"error_type": "protocol", "error_msg": str(e), "service": "OGWS"},
            },
        )
        sys.exit(1)
    except (ConnectionError, TimeoutError, IOError) as e:
        logger.error(
            "Connection/IO error during token setup: %s",
            str(e),
            exc_info=True,
            extra={
                "customer_id": settings.CUSTOMER_ID,
                "asset_id": "auth_service",
                "auth_info": {"error_type": "connection", "error_msg": str(e), "service": "OGWS"},
            },
        )
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(setup_initial_token())
