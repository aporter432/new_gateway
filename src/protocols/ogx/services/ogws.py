"""OGWS API client implementation.

This module provides the core API client for interacting with the OGWS service.
It handles:
- Message submission
- Response validation
- Error handling
- Rate limiting (via server response headers)

Development vs Production:
- Development: Uses test credentials, local rate limiting, flexible validation
- Production: Requires secure credentials, server rate limits, strict validation

For message format and validation rules, see OGWS-1.txt section 2.1.
For rate limiting details, see OGWS-1.txt section 3.2.
For error codes and handling, see OGWS-1.txt section 4.
"""

from typing import Dict

from api.clients.factory import get_ogws_client
from core.app_settings import get_settings
from core.logging.loggers import get_protocol_logger
from protocols.ogx.validation.common.exceptions import OGxProtocolError, ValidationError

logger = get_protocol_logger("ogws_client")
settings = get_settings()


async def submit_ogws_message(payload: Dict) -> Dict:
    """Submit a message to OGWS.

    Args:
        payload: Message payload to submit

    Returns:
        Dict containing response data with at least:
        - ErrorID (int): 0 for success, non-zero for failure
        - ErrorMessage (str): Description if error occurred
        - MessageID (str): Assigned message ID if successful

    Raises:
        ValidationError: If payload validation fails
        OGxProtocolError: If protocol-level errors occur
        ConnectionError: If connection fails
        TimeoutError: If request times out
    """
    try:
        # Validate payload
        if not isinstance(payload, dict):
            raise ValidationError("Payload must be a dictionary")

        # Get OGWS client (handles auth and retries)
        client = await get_ogws_client()

        # Make request
        response = await client.post("/messages", json_data=payload)
        data = await client.handle_response(response)

        # Log outcome
        if data.get("ErrorID", 1) == 0:
            logger.info(
                "Message submitted successfully",
                extra={
                    "message_id": data.get("MessageID"),
                    "customer_id": settings.CUSTOMER_ID,
                },
            )
        else:
            logger.warning(
                "Message submission failed",
                extra={
                    "error_id": data.get("ErrorID"),
                    "error_message": data.get("ErrorMessage"),
                    "customer_id": settings.CUSTOMER_ID,
                },
            )

        return data

    except (ValidationError, OGxProtocolError, ConnectionError, TimeoutError) as e:
        error_msg = f"Error submitting message: {str(e)}"
        logger.error(error_msg, extra={"error": str(e), "customer_id": settings.CUSTOMER_ID})
        return {"ErrorID": 500, "ErrorMessage": error_msg}
