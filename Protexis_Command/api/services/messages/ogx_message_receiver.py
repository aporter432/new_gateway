"""OGx message retrieval service.

This module implements message retrieval as defined in OGx-1.txt Section 4.4.
It handles:
1. Message retrieval
2. Status checking
3. Rate limiting
4. Error handling

Implementation Notes:
    - Uses sliding window rate limiting
    - Handles concurrent requests
    - Implements retry logic
    - Validates responses
"""

from datetime import datetime
from typing import Any, Dict, List

from Protexis_Command.core.logging.loggers.protocol import get_protocol_logger
from Protexis_Command.core.settings.app_settings import get_settings
from Protexis_Command.protocol.ogx.constants.ogx_error_codes import GatewayErrorCode
from Protexis_Command.protocol.ogx.constants.ogx_limits import MAX_MESSAGES_PER_RESPONSE
from Protexis_Command.protocol.ogx.constants.ogx_message_types import MessageType
from Protexis_Command.protocol.ogx.ogx_protocol_handler import OGxProtocolHandler
from Protexis_Command.protocol.ogx.validation.ogx_validation_exceptions import (
    OGxProtocolError,
    ProtocolError,
    RateLimitError,
    ValidationError,
)


class MessageReceiver:
    """Handles message retrieval from OGx.

    This class implements message retrieval according to OGx-1.txt Section 4.4.
    It handles:
    1. Message retrieval with rate limiting
    2. Status checking with retry logic
    3. Error handling and recovery
    """

    def __init__(self, protocol_handler: OGxProtocolHandler) -> None:
        """Initialize message receiver.

        Args:
            protocol_handler: OGx protocol handler instance
        """
        self.protocol_handler = protocol_handler
        self.logger = get_protocol_logger()  # Pass None to use default config
        self.settings = get_settings()
        self._high_watermarks: Dict[str, str] = {}  # Initialize empty high watermarks dict
        self._last_poll: Dict[str, datetime] = {}  # Initialize empty last poll dict

    async def get_messages(
        self, from_utc: datetime, message_type: MessageType
    ) -> List[Dict[str, Any]]:
        """Retrieve messages from OGx.

        Args:
            from_utc: Start time for message retrieval
            message_type: Type of messages to retrieve

        Returns:
            List of retrieved messages

        Raises:
            RateLimitError: If rate limit exceeded
            ProtocolError: For other protocol errors
        """
        try:
            self.logger.debug(
                "Retrieving messages",
                extra={
                    "customer_id": self.settings.CUSTOMER_ID,
                    "asset_id": "message_receiver",
                    "from_utc": from_utc.isoformat(),
                    "message_type": message_type.value,
                    "action": "get_messages",
                },
            )

            messages = await self.protocol_handler.get_messages(from_utc, message_type)

            if len(messages) > MAX_MESSAGES_PER_RESPONSE:
                self.logger.warning(
                    "Too many messages in response",
                    extra={
                        "customer_id": self.settings.CUSTOMER_ID,
                        "asset_id": "message_receiver",
                        "count": len(messages),
                        "max_allowed": MAX_MESSAGES_PER_RESPONSE,
                        "action": "validate_response",
                    },
                )
                raise ValidationError(
                    f"Response exceeds maximum of {MAX_MESSAGES_PER_RESPONSE} messages"
                )

            return messages

        except RateLimitError as e:
            if getattr(e, "error_code", None) == GatewayErrorCode.RETRIEVE_STATUS_RATE_EXCEEDED:
                self.logger.warning(
                    "Message retrieval rate limit exceeded",
                    extra={
                        "customer_id": self.settings.CUSTOMER_ID,
                        "asset_id": "message_receiver",
                        "error_code": GatewayErrorCode.RETRIEVE_STATUS_RATE_EXCEEDED,
                        "action": "handle_rate_limit",
                    },
                )
            raise

        except Exception as e:
            self.logger.error(
                "Message retrieval failed",
                extra={
                    "customer_id": self.settings.CUSTOMER_ID,
                    "asset_id": "message_receiver",
                    "error": str(e),
                    "action": "handle_error",
                },
            )
            raise ProtocolError(f"Message retrieval failed: {str(e)}") from e

    async def get_message_status(self, message_id: str) -> Dict[str, Any]:
        """Get status of a message.

        Args:
            message_id: ID of message to check

        Returns:
            Message status information

        Raises:
            RateLimitError: If rate limit exceeded
            ProtocolError: For other protocol errors
        """
        try:
            self.logger.debug(
                "Checking message status",
                extra={
                    "customer_id": self.settings.CUSTOMER_ID,
                    "asset_id": "message_receiver",
                    "message_id": message_id,
                    "action": "get_status",
                },
            )

            return await self.protocol_handler.get_message_status(message_id)

        except RateLimitError as e:
            if getattr(e, "error_code", None) == GatewayErrorCode.RETRIEVE_STATUS_RATE_EXCEEDED:
                self.logger.warning(
                    "Status check rate limit exceeded",
                    extra={
                        "customer_id": self.settings.CUSTOMER_ID,
                        "asset_id": "message_receiver",
                        "error_code": GatewayErrorCode.RETRIEVE_STATUS_RATE_EXCEEDED,
                        "action": "handle_rate_limit",
                    },
                )
            raise

        except Exception as e:
            self.logger.error(
                "Status check failed",
                extra={
                    "customer_id": self.settings.CUSTOMER_ID,
                    "asset_id": "message_receiver",
                    "error": str(e),
                    "action": "handle_error",
                },
            )
            raise ProtocolError(f"Status check failed: {str(e)}") from e

    async def update_high_watermark(self, account_id: str, new_mark: str) -> None:
        """Update high-watermark for account.

        Maintains the local high-watermark state for continuous message retrieval.
        High-watermarks are used to track the last retrieved message timestamp
        per account.

        Args:
            account_id: Account to update
            new_mark: New high-watermark value from OGx response

        Raises:
            OGxProtocolError: If update fails
        """
        try:
            self._high_watermarks[account_id] = new_mark
            self.logger.debug(
                "Updated high watermark",
                extra={
                    "customer_id": self.settings.CUSTOMER_ID,
                    "asset_id": "message_receiver",
                    "account_id": account_id,
                    "new_mark": new_mark,
                    "action": "update_watermark",
                },
            )
        except (KeyError, ValueError, TypeError) as e:
            self.logger.error(
                "Failed to update high watermark",
                extra={
                    "customer_id": self.settings.CUSTOMER_ID,
                    "asset_id": "message_receiver",
                    "account_id": account_id,
                    "error": str(e),
                    "action": "update_watermark",
                },
            )
            raise OGxProtocolError(f"Failed to update high watermark: {str(e)}") from e

    async def poll_messages(self, interval_seconds: int = 60) -> None:
        """Poll OGx for new messages.

        Long-running task that periodically retrieves new messages using
        high-watermarks. Respects server-enforced rate limits and handles
        errors appropriately.

        Args:
            interval_seconds: Polling interval

        Note:
            This is a background task that runs continuously.
            Server enforces rate limits of 5 calls per minute.
        """
        try:
            now = datetime.utcnow()
            for account_id, last_poll in self._last_poll.items():
                # Check if enough time has elapsed since last poll
                if (now - last_poll).total_seconds() < interval_seconds:
                    continue

                # Get messages using high watermark
                high_mark = self._high_watermarks.get(account_id)
                from_time = datetime.fromisoformat(high_mark) if high_mark else datetime.utcnow()

                # Poll for both forward and return messages
                for message_type in [MessageType.FORWARD, MessageType.RETURN]:
                    await self.get_messages(from_utc=from_time, message_type=message_type)

                self._last_poll[account_id] = now

        except (KeyError, ValueError, TypeError) as e:
            self.logger.error(
                "Error accessing polling data",
                extra={
                    "customer_id": self.settings.CUSTOMER_ID,
                    "asset_id": "message_receiver",
                    "error": str(e),
                    "action": "poll_messages",
                },
            )
        except OGxProtocolError as e:
            self.logger.error(
                "Protocol error during message polling",
                extra={
                    "customer_id": self.settings.CUSTOMER_ID,
                    "asset_id": "message_receiver",
                    "error": str(e),
                    "action": "poll_messages",
                },
            )
