"""Background worker for processing message queue.

This module provides:
- Asynchronous message processing
- Automatic retry handling
- Error recovery
- Health monitoring
"""

import asyncio
from typing import Optional

from core.app_settings import Settings, get_settings
from core.logging.loggers import get_infra_logger
from core.message_queue import MessageQueue
from infrastructure.redis import get_redis_client
from protocols.ogx.services.ogws import submit_ogws_message


class MessageWorker:
    """Background worker for processing messages."""

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

    async def start(self) -> None:
        """Start the worker process."""
        if self.running:
            return

        self.running = True
        self.current_task = asyncio.create_task(self._process_queue())
        self.logger.info("Message worker started")

    async def stop(self) -> None:
        """Stop the worker process."""
        self.running = False
        if self.current_task:
            self.current_task.cancel()
            try:
                await self.current_task
            except asyncio.CancelledError:
                pass
        self.logger.info("Message worker stopped")

    async def _process_queue(self) -> None:
        """Main processing loop."""
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

                        # Submit to OGWS
                        response = await submit_ogws_message(
                            message.payload, base_url=self.settings.OGWS_BASE_URL
                        )

                        # Check response
                        if response.get("ErrorID", 1) == 0:
                            await self.message_queue.mark_delivered(message.message_id)
                        else:
                            error = response.get("ErrorMessage", "Unknown error")
                            await self.message_queue.mark_failed(message.message_id, error)

                    except Exception as e:
                        await self.message_queue.mark_failed(
                            message.message_id, f"Processing error: {str(e)}"
                        )

                # Sleep if no messages
                if not messages:
                    await asyncio.sleep(5)

            except Exception as e:
                self.logger.error(
                    f"Error in message processing loop: {str(e)}", extra={"error": str(e)}
                )
                await asyncio.sleep(5)  # Sleep on error to prevent tight loop


async def get_message_worker() -> MessageWorker:
    """Get configured message worker instance."""
    settings = get_settings()
    redis = await get_redis_client()
    message_queue = MessageQueue(redis, settings)
    return MessageWorker(settings, message_queue)
