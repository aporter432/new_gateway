"""Message receiving and polling management for OGWS.

This module implements the Service Provider (SP) side of OGWS message retrieval.
It handles responses from the OGWS server while respecting server-enforced limits
and specifications.

Source of Truth:
- OGWS-1.txt Section 2.3: Message Retention and Limitations
    - Production: Server enforces 5-day retention
    - Development: Test messages may persist longer
- OGWS-1.txt Section 3.4: Access Throttling
    - Production: Server enforces strict rate limits
    - Development: Local simulation of limits
- OGWS-1.txt Section 4.2: Rate Limiting and Quotas
    - Production: 5 calls per 60 seconds, server-enforced
    - Development: Configurable limits via settings

Environment-Specific Behavior:
Development:
    - Uses test credentials (70000934/password)
    - Local rate limit simulation
    - Mock responses via proxy
    - Debug-level logging enabled
    - Flexible validation rules
    - Extended message retention

Production:
    - Secure credentials from environment
    - Server-enforced rate limits
    - Direct HTTPS connection
    - Info/Error logging only
    - Strict validation
    - 5-day message retention

Production Transition Requirements:
1. Authentication:
   - Remove test credentials
   - Implement secure credential management
   - Enable TLS certificate validation

2. Rate Limiting:
   - Remove local rate limit simulation
   - Implement proper backoff handling
   - Add rate limit monitoring

3. Validation:
   - Enable strict message validation
   - Add production error codes
   - Implement proper error handling

4. Networking:
   - Remove debug proxy
   - Enable TLS verification
   - Implement connection pooling

5. Logging:
   - Disable debug logging
   - Enable secure audit logging
   - Implement proper PII handling

For detailed specifications, see OGWS-1.txt sections:
- 2.3: Message Retention and Limitations
- 3.4: Access Throttling
- 4.2: Rate Limiting and Quotas
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import httpx

from core.app_settings import get_settings
from core.logging.loggers import get_protocol_logger
from protocols.ogx.constants.limits import (
    ERR_RETRIEVE_STATUS_RATE_EXCEEDED,
    MAX_MESSAGES_PER_RESPONSE,
)
from protocols.ogx.exceptions import OGxProtocolError, ValidationError


class MessageReceiver:
    """Handles message receiving from OGWS.

    This class implements the SP side of message retrieval, focusing on handling
    server responses and maintaining proper state rather than enforcing server-side
    rules which are already handled by OGWS.

    Implementation follows OGWS-1.txt specifications:

    Development Environment:
        - Uses test endpoints via proxy
        - All logging levels enabled
        - Local rate limit tracking
        - Simulated high-watermarks
        - Mock responses allowed
        - Flexible validation

    Production Environment:
        - Direct HTTPS connection
        - Info/Error logging only
        - Server-enforced limits
        - Persistent high-watermarks
        - Strict response validation
        - Full error handling

    Key Responsibilities:
    - Message retrieval with proper error handling
    - High-watermark tracking for continuous retrieval
    - Status updates and tracking
    - Rate limit and error response handling

    Note:
        This implementation assumes server-side enforcement of:
        - Message retention periods (5 days in production)
        - Rate limiting (5 calls/60s in production)
        - Access throttling (server-controlled)
        - Batch size limits (500 messages max)
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
        """Get messages from OGWS.

        Args:
            from_iso_timestamp: Optional high watermark timestamp
            include_types: Whether to include message types
            include_raw: Whether to include raw payload

        Returns:
            List of message dictionaries

        Raises:
            ValidationError: If response exceeds message limit
            OGxProtocolError: If retrieval fails
        """
        try:
            # Construct params with correct types
            params: Dict[str, Union[str, bool]] = {
                "FromUTC": from_iso_timestamp or datetime.utcnow().isoformat(),
                "IncludeTypes": str(include_types).lower(),
                "IncludeRawPayload": str(include_raw).lower(),
            }

            self.logger.debug(
                "Retrieving messages",
                extra={
                    "customer_id": self.settings.CUSTOMER_ID,
                    "asset_id": "message_receiver",
                    "from_utc": params["FromUTC"],
                    "action": "get_messages",
                },
            )

            # Make API call to OGWS
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.settings.OGWS_BASE_URL}/messages",
                    params=params,
                    headers={"Content-Type": "application/json"},
                )
                response.raise_for_status()
                data = response.json()
                messages: List[Dict[str, Any]] = data.get("Messages", [])

            if len(messages) > MAX_MESSAGES_PER_RESPONSE:
                raise ValidationError(
                    f"Response exceeds maximum of {MAX_MESSAGES_PER_RESPONSE} messages"
                )
            return messages

        except OGxProtocolError as e:
            if getattr(e, "error_code", None) == ERR_RETRIEVE_STATUS_RATE_EXCEEDED:
                self.logger.warning(
                    "Rate limit exceeded during message retrieval",
                    extra={
                        "customer_id": self.settings.CUSTOMER_ID,
                        "asset_id": "message_receiver",
                        "error": str(e),
                        "error_code": ERR_RETRIEVE_STATUS_RATE_EXCEEDED,
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
            raise OGxProtocolError(f"Failed to retrieve messages: {str(e)}") from e

    async def update_high_watermark(self, account_id: str, new_mark: str) -> None:
        """Update high-watermark for account.

        Maintains the local high-watermark state for continuous message retrieval.
        High-watermarks are used to track the last retrieved message timestamp
        per account.

        Args:
            account_id: Account to update
            new_mark: New high-watermark value from OGWS response

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

    async def get_message_status(self, message_ids: List[int]) -> List[Dict[str, Any]]:
        """Get status of messages.

        Args:
            message_ids: List of message IDs to check

        Returns:
            List of status dictionaries
        """
        try:
            self.logger.debug(
                "Retrieving message status",
                extra={
                    "customer_id": self.settings.CUSTOMER_ID,
                    "asset_id": "message_receiver",
                    "message_ids": message_ids,
                    "action": "get_status",
                },
            )

            # Make API call to OGWS
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.settings.OGWS_BASE_URL}/messages/status",
                    params={"ids": ",".join(str(id) for id in message_ids)},
                    headers={"Content-Type": "application/json"},
                )
                response.raise_for_status()
                data = response.json()
                statuses: List[Dict[str, Any]] = data.get("Statuses", [])
                return statuses

        except OGxProtocolError as e:
            if getattr(e, "error_code", None) == ERR_RETRIEVE_STATUS_RATE_EXCEEDED:
                self.logger.warning(
                    "Rate limit exceeded during status retrieval",
                    extra={
                        "customer_id": self.settings.CUSTOMER_ID,
                        "asset_id": "message_receiver",
                        "message_ids": message_ids,
                        "error": str(e),
                        "error_code": ERR_RETRIEVE_STATUS_RATE_EXCEEDED,
                        "action": "get_status",
                    },
                )
            raise

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
            raise OGxProtocolError(f"Failed to retrieve message status: {str(e)}") from e

    async def poll_messages(self, interval_seconds: int = 60) -> None:
        """Poll OGWS for new messages.

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
                await self.get_messages(from_iso_timestamp=high_mark)
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
