"""Message receiving and polling management for OGWS.

This module handles:
- Inbound message retrieval from OGWS
- High-watermark tracking
- Message polling implementation
- Error handling for retrievals

For detailed specifications, see:
- protocols.ogx.constants.limits: Message retention and batch sizes
- protocols.ogx.constants.message_states: Message format examples
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from core.app_settings import get_settings
from core.logging.loggers import get_protocol_logger
from protocols.ogx.constants.limits import (
    DEFAULT_CALLS_PER_MINUTE,
    MAX_MESSAGES_PER_RESPONSE,
    MESSAGE_RETENTION_DAYS,
)
from protocols.ogx.constants.http_errors import HTTPError

class MessageReceiver:
    """Handles message receiving from OGWS.

    Implements message retrieval following OGWS-1.txt specifications.
    For message retention and limits, see protocols.ogx.constants.limits.
    For message format examples, see protocols.ogx.constants.message_states.
    """

    def __init__(self) -> None:
        """Initialize message receiver."""
        self._high_watermarks: Dict[str, str] = {}  # Track high-watermarks per account
        self._last_poll: Dict[str, datetime] = {}  # Track last poll times per account
        self.logger = get_protocol_logger("message_receiver")
        self.settings = get_settings()

    async def get_messages(
        self,
        from_iso_timestamp: Optional[str] = None,
        include_types: bool = False,
        include_raw: bool = False,
    ) -> List[Dict[str, Any]]:
        """Retrieve messages from OGWS.

        Follows OGWS-1.txt retrieval specifications:
        - Maximum MESSAGE_RETENTION_DAYS history
        - Maximum MAX_MESSAGES_PER_RESPONSE messages per call
        - Uses high-watermark for continuous retrieval

        Args:
            from_iso_timestamp: Starting time for message retrieval
            include_types: Include field types in response
            include_raw: Include raw payloads

        Returns:
            List of messages in format:
            [{
                "ID": 10844864715,
                "MessageUTC": "2022-11-25 12:00:03",
                "MobileID": "01008988SKY5909",
                "Payload": {
                    "Name": "message_name",
                    "SIN": 128,
                    "MIN": 1,
                    "Fields": [...]
                }
            }]

        Raises:
            RateLimitExceeded: If ERR_RETRIEVE_STATUS_RATE_EXCEEDED received
            MessageRetrievalError: If retrieval fails
        """
        try:
            params = {
                "FromUTC": from_iso_timestamp or datetime.utcnow().isoformat(),
                "IncludeTypes": include_types,
                "IncludeRawPayload": include_raw,
            }

            self.logger.info(
                "Retrieving messages",
                extra={
                    "customer_id": self.settings.CUSTOMER_ID,
                    "asset_id": "message_receiver",
                    "from_utc": params["FromUTC"],
                    "action": "get_messages",
                },
            )

            # TODO: Make actual API call to OGWS here
            # For now, return empty list to satisfy interface
            return []

        except HTTPError.TOO_MANY_REQUESTS as e:
            self.logger.warning(
                "Rate limit exceeded during message retrieval",
                extra={
                    "customer_id": self.settings.CUSTOMER_ID,
                    "asset_id": "message_receiver",
                    "error": str(e),
                    "action": "get_messages",
                },
            )
            raise

        except Exception as e:
            self.logger.error(
                "Failed to retrieve messages",
                extra={
                    "customer_id": self.settings.CUSTOMER_ID,
                    "asset_id": "message_receiver",
                    "error": str(e),
                    "action": "get_messages",
                },
            )
            raise MessageRetrievalError(f"Failed to retrieve messages: {str(e)}") from e

    async def update_high_watermark(self, account_id: str, new_mark: str) -> None:
        """Update high-watermark for account.

        Manages high-watermark as specified in OGWS-1.txt:
        - Store per account
        - Use for continuous message retrieval
        - Reset after MESSAGE_RETENTION_DAYS

        Args:
            account_id: Account to update
            new_mark: New high-watermark value from OGWS response
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
        except Exception as e:
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

    async def get_message_status(self, message_ids: List[int]) -> List[Dict[str, Any]]:
        """Get status of submitted messages.

        Follows OGWS-1.txt status retrieval limits:
        - Maximum MAX_STATUS_IDS_PER_REQUEST IDs per request
        - Subject to ERR_RETRIEVE_STATUS_RATE_EXCEEDED limit

        Args:
            message_ids: IDs of messages to check

        Returns:
            List of message statuses in format:
            [{
                "ID": 10844864715,
                "State": 1,  # RECEIVED
                "IsClosed": true,
                "Transport": 1,  # SATELLITE
                "CreateUTC": "2022-11-25 12:00:20"
            }]
        """
        try:
            self.logger.info(
                "Retrieving message status",
                extra={
                    "customer_id": self.settings.CUSTOMER_ID,
                    "asset_id": "message_receiver",
                    "message_ids": message_ids,
                    "action": "get_status",
                },
            )

            # TODO: Make actual API call to OGWS here
            # For now, return empty list to satisfy interface
            return []

        except Exception as e:
            self.logger.error(
                "Failed to retrieve message status",
                extra={
                    "customer_id": self.settings.CUSTOMER_ID,
                    "asset_id": "message_receiver",
                    "message_ids": message_ids,
                    "error": str(e),
                    "action": "get_status",
                },
            )
            raise MessageRetrievalError(f"Failed to retrieve message status: {str(e)}") from e

    async def poll_messages(self, interval_seconds: int = 60) -> None:
        """Poll OGWS for new messages.

        Implements polling following OGWS-1.txt guidelines:
        - Respect DEFAULT_CALLS_PER_MINUTE limit
        - Use high-watermark for continuous retrieval
        - Handle rate limit errors with backoff

        Args:
            interval_seconds: Polling interval

        Note:
            This is a long-running task that should be run in the background
        """
        try:
            now = datetime.utcnow()
            for account_id, last_poll in self._last_poll.items():
                # Check if enough time has elapsed since last poll
                if (now - last_poll).total_seconds() < interval_seconds:
                    continue

                # Get messages using high watermark
                high_mark = self._high_watermarks.get(account_id)
                await self.get_messages(from_iso_timestamp=high_mark)
                self._last_poll[account_id] = now

        except Exception as e:
            self.logger.error(
                "Error during message polling",
                extra={
                    "customer_id": self.settings.CUSTOMER_ID,
                    "asset_id": "message_receiver",
                    "error": str(e),
                    "action": "poll_messages",
                },
            )
