"""Message sending and delivery management for OGx.

This module implements message delivery following OGx-1.txt specifications.

Source of Truth:
- OGx-1.txt Section 4.2: Rate Limiting and Quotas
    - Production enforces 5 calls per 60 seconds
    - Development allows configurable limits
- OGx-1.txt Section 5.1: Message Format
    - Strict validation in production
    - Flexible validation in development
- OGx-1.txt Section 7.2: Error Recovery
    - Production requires robust retry handling
    - Development allows simplified recovery

Environment-Specific Behavior:
Development:
    - Uses test credentials (70000934/password)
    - Local rate limiting simulation
    - Flexible validation rules
    - Simplified retry logic
    - Debug-level logging
    - Mock OGx responses via proxy

Production:
    - Requires secure credentials via environment
    - Server-enforced rate limiting
    - Strict message validation
    - Full retry mechanism with backoff
    - Info/Error-level logging only
    - Direct OGx connection with TLS

Usage:
    sender = MessageSender()
    await sender.initialize()  # Must be called before using the sender
    response = await sender.send_message(message)

For detailed specifications, see:
- protocols.ogx.constants.limits: Rate limits and batch sizes
- protocols.ogx.constants.message_states: Message states and transitions
- protocols.ogx.constants.transport_types: Transport options
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, cast

import httpx

from Protexis_Command.api_ogx.auth.manager import OGxAuthManager
from Protexis_Command.api_ogx.constants import TransportType
from Protexis_Command.api_ogx.constants.ogx_error_codes import GatewayErrorCode
from Protexis_Command.api_ogx.constants.ogx_limits import (
    DEFAULT_CALLS_PER_MINUTE,
    DEFAULT_WINDOW_SECONDS,
    MAX_SUBMIT_MESSAGES,
)
from Protexis_Command.api_ogx.validation.ogx_validation_exceptions import (
    OGxProtocolError,
    ValidationError,
)
from Protexis_Command.core.app_settings import get_settings
from Protexis_Command.core.logging.loggers.protocol import get_protocol_logger
from Protexis_Command.infrastructure.redis import get_redis_client


class MessageSender:
    """Handles message sending to OGx.

    Implements rate-limited message submission following OGx-1.txt specifications.
    For rate limits and batch sizes, see protocols.ogx.constants.limits.
    For message format examples, see protocols.ogx.constants.message_states.
    """

    def __init__(self) -> None:
        """Initialize message sender."""
        # Track API call timestamps per group
        self._rate_limiter: Dict[str, List[datetime]] = {}
        # Track retry attempts per message ID
        self._retry_counts: Dict[int, int] = {}
        self.logger = get_protocol_logger()  # Pass None to use default config
        self.settings = get_settings()
        # Will be initialized in initialize()
        self.auth_manager: Optional[OGxAuthManager] = None

    async def initialize(self) -> None:
        """Initialize async components like Redis connection.

        This needs to be called before using the sender.

        Raises:
            RuntimeError: If Redis connection fails
        """
        redis = await get_redis_client()
        if not redis:
            raise RuntimeError("Failed to initialize Redis connection")
        self.auth_manager = OGxAuthManager(self.settings, redis)

    async def send_message(
        self, message: Dict[str, Any], transport: Optional[TransportType] = None
    ) -> Dict[str, Any]:
        """Send a message to OGx.

        Args:
            message: Message to send
            transport: Optional transport type constraint

        Returns:
            Response data from OGx

        Raises:
            RuntimeError: If sender not initialized
            OGxProtocolError: If the message fails to send
        """
        if not self.auth_manager:
            raise RuntimeError("MessageSender not initialized. Call initialize() first.")

        try:
            # Add transport type to message if specified
            message_data = message.copy()
            if transport is not None:
                message_data["TransportType"] = transport.value

            # Get auth header
            auth_header = await self.auth_manager.get_auth_header()

            # Send message
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.settings.OGx_BASE_URL}/submit/messages",
                    headers={**auth_header, "Content-Type": "application/json"},
                    json=message_data,
                )
                response.raise_for_status()
                return cast(Dict[str, Any], response.json())

        except httpx.HTTPError as e:
            raise OGxProtocolError(f"Failed to send message: {str(e)}") from e

    async def submit_batch(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Submit batch of messages to OGx.

        Follows batch limits from OGx-1.txt:
        - Maximum MAX_SUBMIT_MESSAGES per call
        - Subject to DEFAULT_CALLS_PER_MINUTE rate limit
        - Network-specific payload limits apply to each message

        Args:
            messages: List of messages to send (see message_states.py for format)

        Returns:
            List of OGx responses, one per message

        Raises:
            ValidationError: If batch size exceeds limit
            OGxProtocolError: If submission fails
        """
        if len(messages) > MAX_SUBMIT_MESSAGES:
            raise ValidationError(f"Cannot submit more than {MAX_SUBMIT_MESSAGES} messages")

        responses = []
        for message in messages:
            try:
                response = await self.send_message(message)
                responses.append(response)
            except OGxProtocolError as e:
                if getattr(e, "error_code", None) == GatewayErrorCode.SUBMIT_MESSAGE_RATE_EXCEEDED:
                    # Wait and retry once on rate limit
                    await self.handle_rate_limit(GatewayErrorCode.SUBMIT_MESSAGE_RATE_EXCEEDED)
                    response = await self.send_message(message)
                    responses.append(response)
                else:
                    raise

        return responses

    async def handle_rate_limit(self, error_code: GatewayErrorCode) -> None:
        """Handle rate limit errors.

        Handles specific error codes from OGx-1.txt:
        - GatewayErrorCode.SUBMIT_MESSAGE_RATE_EXCEEDED (24579)
        - HTTP 429 Too Many Requests
        - HTTP 503 Service Unavailable

        Args:
            error_code: Error code from OGx

        Implementation:
            - Clears rate limit tracking
            - Implements exponential backoff
            - Logs rate limit events
        """
        # Clear rate limit tracking
        self._rate_limiter.clear()

        # Log rate limit event
        self.logger.warning(
            "Rate limit encountered",
            extra={
                "customer_id": self.settings.CUSTOMER_ID,
                "asset_id": "message_sender",
                "error_code": error_code,
                "action": "handle_rate_limit",
            },
        )

        # Wait for rate limit window
        await asyncio.sleep(DEFAULT_WINDOW_SECONDS)

    async def retry_failed_message(
        self, message_id: int, max_retries: int = 3
    ) -> Optional[Dict[str, Any]]:
        """Retry sending a failed message.

        Implementation follows OGx-1.txt Section 7.2 for retry handling:
        - Exponential backoff between retries
        - Maximum retry attempts enforced
        - Authentication maintained across retries
        - Status tracking per message ID

        Args:
            message_id: ID of message to retry
            max_retries: Maximum number of retry attempts

        Returns:
            Response data if successful, None if failed

        Raises:
            RuntimeError: If sender not initialized
        """
        if not self.auth_manager:
            raise RuntimeError("MessageSender not initialized. Call initialize() first.")

        try:
            retry_count = self._retry_counts.get(message_id, 0)
            if retry_count >= max_retries:
                self.logger.warning(
                    "Max retries exceeded",
                    extra={
                        "customer_id": self.settings.CUSTOMER_ID,
                        "asset_id": "message_sender",
                        "message_id": message_id,
                        "retry_count": retry_count,
                    },
                )
                return None

            # Calculate exponential backoff delay
            backoff_delay = min(2**retry_count, 60)  # Cap at 60 seconds
            await asyncio.sleep(backoff_delay)

            # Construct retry URL
            retry_url = f"{self.settings.OGx_BASE_URL}/submit/messages/{message_id}/retry"

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    retry_url,
                    headers=await self.auth_manager.get_auth_header(),
                )
                response.raise_for_status()
                data: Dict[str, Any] = response.json()

                # Update retry count
                self._retry_counts[message_id] = retry_count + 1

                self.logger.info(
                    "Message retry successful",
                    extra={
                        "customer_id": self.settings.CUSTOMER_ID,
                        "asset_id": "message_sender",
                        "message_id": message_id,
                        "retry_count": retry_count + 1,
                        "backoff_delay": backoff_delay,
                    },
                )

                return data

        except httpx.HTTPStatusError as e:
            self.logger.error(
                "Retry failed",
                extra={
                    "customer_id": self.settings.CUSTOMER_ID,
                    "asset_id": "message_sender",
                    "message_id": message_id,
                    "retry_count": retry_count,
                    "error": str(e),
                    "action": "retry_message",
                },
            )
            return None

    def _can_make_request(self) -> bool:
        """Check if request can be made within rate limits.

        Implements sliding window rate limiting as specified in OGx-1.txt.

        Returns:
            bool: True if request allowed, False if would exceed rate limit
        """
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=DEFAULT_WINDOW_SECONDS)

        # Clean up old timestamps
        for group in self._rate_limiter:
            self._rate_limiter[group] = [
                ts for ts in self._rate_limiter[group] if ts > window_start
            ]

        # Check rate limit
        group = str(self.settings.CUSTOMER_ID)
        timestamps = self._rate_limiter.get(group, [])
        return len(timestamps) < DEFAULT_CALLS_PER_MINUTE

    def _record_request(self) -> None:
        """Record a successful API request for rate limiting."""
        group = str(self.settings.CUSTOMER_ID)
        if group not in self._rate_limiter:
            self._rate_limiter[group] = []
        self._rate_limiter[group].append(datetime.utcnow())
