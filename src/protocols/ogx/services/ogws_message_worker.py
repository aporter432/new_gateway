"""Background worker for processing message queue.

This module provides:
- Asynchronous message processing
- Automatic retry handling with exponential backoff
- Error recovery with dead letter queue
- Health monitoring and metrics

Development vs Production:
- Development: Simplified retry logic, all logging levels, mock responses
- Production: Full retry mechanism, info/error logging, direct OGWS connection

For retry policies, see OGWS-1.txt section 3.3.
For error handling, see OGWS-1.txt section 4.2.
"""

import asyncio
import time
from typing import Dict, Optional

from core.app_settings import Settings, get_settings
from core.logging.loggers import get_infra_logger
from infrastructure.redis import get_redis_client
from protocols.ogx.constants import GatewayErrorCode
from protocols.ogx.constants.limits import DEFAULT_WINDOW_SECONDS
from protocols.ogx.validation.common.exceptions import OGxProtocolError
from protocols.ogx.services.ogws import submit_ogws_message
from protocols.ogx.services.ogws_message_queue import MessageQueue


class MessageWorker:
    """Background worker for processing messages.

    Features:
    - Asynchronous processing with configurable batch size
    - Exponential backoff for retries
    - Health monitoring via metrics
    - Dead letter queue for failed messages
    - Rate limit compliance
    """

    def __init__(self, settings: Settings, message_queue: MessageQueue):
        """Initialize worker.

        Args:
            settings: Application settings
            message_queue: Message queue manager
        """
        self.settings = settings
        self.message_queue = message_queue
        self.logger = get_infra_logger("message_worker")
        self.running = False
        self.current_task: Optional[asyncio.Task] = None

        # Health metrics
        self.last_successful_process = 0.0
        self.processed_count = 0
        self.error_count = 0
        self.retry_count = 0

    async def start(self) -> None:
        """Start the worker process."""
        if self.running:
            return

        self.running = True
        self.current_task = asyncio.create_task(self._process_queue())
        self.logger.info(
            "Message worker started",
            extra={"customer_id": self.settings.CUSTOMER_ID, "worker_id": id(self)},
        )

    async def stop(self) -> None:
        """Stop the worker process."""
        self.running = False
        if self.current_task:
            self.current_task.cancel()
            try:
                await self.current_task
            except asyncio.CancelledError:
                pass
        self.logger.info(
            "Message worker stopped",
            extra={
                "customer_id": self.settings.CUSTOMER_ID,
                "worker_id": id(self),
                "processed_count": self.processed_count,
                "error_count": self.error_count,
            },
        )

    def get_health_metrics(self) -> Dict:
        """Get current health metrics."""
        return {
            "running": self.running,
            "last_successful_process": self.last_successful_process,
            "processed_count": self.processed_count,
            "error_count": self.error_count,
            "retry_count": self.retry_count,
            "uptime": (
                time.time() - self.last_successful_process if self.last_successful_process else 0
            ),
        }

    async def _process_queue(self) -> None:
        """Main processing loop with retry and error handling."""
        while self.running:
            try:
                # Get batch of pending messages
                messages = await self.message_queue.get_pending_messages()

                for message in messages:
                    if not self.running:
                        break

                    try:
                        # Mark as in progress
                        await self.message_queue.mark_in_progress(message.message_id)

                        # Calculate retry delay with exponential backoff
                        retry_delay = 0
                        if message.retry_count > 0:
                            retry_delay = min(
                                DEFAULT_WINDOW_SECONDS * (2 ** (message.retry_count - 1)),
                                300,  # Max 5 minutes
                            )
                            await asyncio.sleep(retry_delay)

                        # Submit to OGWS
                        response = await submit_ogws_message(message.payload)

                        # Handle rate limiting using existing error code
                        if (
                            response.get("ErrorID")
                            == GatewayErrorCode.SUBMIT_MESSAGE_RATE_EXCEEDED
                        ):
                            retry_after = response.get("RetryAfter", 60)
                            self.logger.warning(
                                "Rate limited, will retry",
                                extra={
                                    "message_id": message.message_id,
                                    "retry_after": retry_after,
                                    "retry_count": message.retry_count,
                                },
                            )
                            await asyncio.sleep(retry_after)
                            await self.message_queue.mark_failed(
                                message.message_id, f"Rate limited. Retry after {retry_after}s"
                            )
                            self.retry_count += 1
                            continue

                        # Check response
                        if response.get("ErrorID", 1) == 0:
                            await self.message_queue.mark_delivered(message.message_id)
                            self.processed_count += 1
                            self.last_successful_process = time.time()
                        else:
                            error = response.get("ErrorMessage", "Unknown error")
                            await self.message_queue.mark_failed(message.message_id, error)
                            self.error_count += 1
                            self.logger.error(
                                "Message processing failed",
                                extra={
                                    "message_id": message.message_id,
                                    "error": error,
                                    "retry_count": message.retry_count,
                                },
                            )

                    except asyncio.CancelledError:
                        self.logger.info("Message processing cancelled")
                        await self.message_queue.mark_failed(
                            message.message_id, "Processing cancelled"
                        )
                        raise
                    except OGxProtocolError as e:
                        self.error_count += 1
                        await self.message_queue.mark_failed(
                            message.message_id, f"Protocol error: {str(e)}"
                        )
                        self.logger.error(
                            "Protocol error processing message",
                            extra={
                                "message_id": message.message_id,
                                "error": str(e),
                                "error_code": e.error_code,
                                "retry_count": message.retry_count,
                            },
                        )
                    except (ConnectionError, TimeoutError) as e:
                        self.error_count += 1
                        await self.message_queue.mark_failed(
                            message.message_id, f"Network error: {str(e)}"
                        )
                        self.logger.error(
                            "Network error processing message",
                            extra={
                                "message_id": message.message_id,
                                "error": str(e),
                                "retry_count": message.retry_count,
                            },
                        )

                # Sleep if no messages to prevent tight loop
                if not messages:
                    await asyncio.sleep(5)

            except asyncio.CancelledError:
                self.logger.info("Message processing loop cancelled")
                self.running = False
                raise
            except OGxProtocolError as e:
                self.error_count += 1
                self.logger.error(
                    "Protocol error in message processing loop",
                    extra={
                        "error": str(e),
                        "error_code": e.error_code,
                        "customer_id": self.settings.CUSTOMER_ID,
                    },
                )
                await asyncio.sleep(5)
            except (ConnectionError, TimeoutError) as e:
                self.error_count += 1
                self.logger.error(
                    "Network error in message processing loop",
                    extra={"error": str(e), "customer_id": self.settings.CUSTOMER_ID},
                )
                await asyncio.sleep(5)


async def get_message_worker() -> MessageWorker:
    """Get configured message worker instance."""
    settings = get_settings()
    redis = await get_redis_client()
    message_queue = MessageQueue(redis, settings)
    return MessageWorker(settings, message_queue)
