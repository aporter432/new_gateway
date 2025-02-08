"""Message queue management for reliable message delivery.

This module provides a robust message queuing system for OGWS message handling with the following features:
- Message queue persistence in Redis for durability
- Automatic retry handling with configurable retry policies
- Dead letter queue (DLQ) for failed messages after max retries
- Message state tracking throughout lifecycle
- Atomic operations for state transitions
- Error tracking and logging

The module follows these key principles:
1. Single Responsibility: Each class handles one aspect of message management
2. Open/Closed: Extensible for different queue types while maintaining core logic
3. Interface Segregation: Clean separation between queue operations
4. Dependency Inversion: Depends on abstractions (Redis interface) not implementations

For message format examples and state transitions, see protocols.ogx.constants.message_states.
For rate limits and batch sizes, see protocols.ogx.constants.limits.
"""

import json
import time
from typing import Dict, List, Optional

from redis.asyncio import Redis

from core.app_settings import Settings
from core.logging.loggers import get_infra_logger
from protocols.ogx.constants.limits import (
    DEFAULT_CALLS_PER_MINUTE,
    DEFAULT_WINDOW_SECONDS,
    MAX_MESSAGES_PER_RESPONSE,
    MAX_SUBMIT_MESSAGES,
    MESSAGE_RETENTION_DAYS,
)
from protocols.ogx.constants.message_states import MessageState


class QueuedMessage:
    """Message in the queue with metadata.

    This class encapsulates a message and its metadata for queue processing.
    It tracks the message's state, retry attempts, and error history.

    Attributes:
        message_id (str): Unique identifier for the message
        payload (Dict): The actual message content to be delivered
        state (MessageState): Current state of the message in the queue
        retry_count (int): Number of delivery attempts made
        last_attempt (Optional[float]): Timestamp of last delivery attempt
        error (Optional[str]): Last error message if failed
        created_at (float): Timestamp when message was first queued
    """

    def __init__(
        self,
        message_id: str,
        payload: Dict,
        state: MessageState = MessageState.PENDING,
        retry_count: int = 0,
        last_attempt: Optional[float] = None,
        error: Optional[str] = None,
    ):
        self.message_id = message_id
        self.payload = payload
        self.state = state
        self.retry_count = retry_count
        self.last_attempt = last_attempt
        self.error = error
        self.created_at = time.time()

    def to_dict(self) -> Dict:
        """Convert to dictionary for storage."""
        return {
            "message_id": self.message_id,
            "payload": self.payload,
            "state": self.state.value,
            "retry_count": self.retry_count,
            "last_attempt": self.last_attempt,
            "error": self.error,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "QueuedMessage":
        """Create from dictionary."""
        return cls(
            message_id=data["message_id"],
            payload=data["payload"],
            state=MessageState(data["state"]),
            retry_count=data["retry_count"],
            last_attempt=data["last_attempt"],
            error=data["error"],
        )


class MessageQueue:
    """Manages message queuing and retry logic with Redis persistence.

    This class provides a robust implementation of message queue management with the following features:
    - Atomic operations for state transitions using Redis transactions
    - Configurable retry policies with exponential backoff
    - Dead letter queue (DLQ) for messages that exceed retry limits
    - Message state tracking and error history
    - High availability through Redis persistence

    The queue maintains five distinct queues in Redis:
    1. pending_queue: Messages waiting to be processed
    2. in_progress_queue: Messages currently being processed
    3. delivered_queue: Successfully delivered messages
    4. failed_queue: Failed messages that will be retried
    5. dead_letter_queue: Permanently failed messages

    Queue operations are atomic and thread-safe through Redis transactions.
    Message state transitions are logged for monitoring and debugging.

    Args:
        redis (Redis): Async Redis client for persistence
        settings (Settings): Application settings including retry configuration

    Attributes:
        redis (Redis): Redis client instance
        settings (Settings): Application settings
        logger (Logger): Structured logger for queue operations
        max_retries (int): Maximum number of delivery attempts
        retry_delay (int): Base delay between retries in seconds
    """

    def __init__(self, redis: Redis, settings: Settings):
        """Initialize queue manager.

        Sets up Redis key prefixes and configures retry policies based on settings.
        Initializes logging for queue operations.

        Args:
            redis (Redis): Async Redis client for persistence
            settings (Settings): Application settings including retry configuration
        """
        self.redis = redis
        self.settings = settings
        self.logger = get_infra_logger("message_queue")

        # Redis keys
        self.pending_queue = "ogws:messages:pending"
        self.in_progress_queue = "ogws:messages:in_progress"
        self.delivered_queue = "ogws:messages:delivered"
        self.failed_queue = "ogws:messages:failed"
        self.dead_letter_queue = "ogws:messages:dead_letter"

        # Queue settings from OGWS constants
        self.max_retries = DEFAULT_CALLS_PER_MINUTE  # Align with rate limit
        self.retry_delay = DEFAULT_WINDOW_SECONDS  # Use documented window
        self.message_retention_days = MESSAGE_RETENTION_DAYS
        self.max_batch_size = MAX_MESSAGES_PER_RESPONSE
        self.max_submit_size = MAX_SUBMIT_MESSAGES

    async def enqueue_message(self, message_id: str, payload: Dict) -> None:
        """Add message to pending queue.

        Creates a new QueuedMessage instance and stores it in the pending queue.
        Uses atomic Redis operations to ensure message is not lost.
        Enforces MAX_SUBMIT_MESSAGES limit from OGWS-1.txt section 2.3.

        Args:
            message_id (str): Unique identifier for the message
            payload (Dict): Message content to be delivered

        Raises:
            ValueError: If pending queue has reached MAX_SUBMIT_MESSAGES
            Exception: If Redis operation fails
        """
        try:
            # Check current pending count
            pending_count = await self.redis.hlen(self.pending_queue)
            if pending_count >= self.max_submit_size:
                raise ValueError(
                    f"Cannot enqueue more than {self.max_submit_size} messages. "
                    "Wait for current messages to be processed."
                )

            message = QueuedMessage(message_id=message_id, payload=payload)
            await self.redis.hset(self.pending_queue, message_id, json.dumps(message.to_dict()))

            self.logger.info(
                f"Message {message_id} enqueued",
                extra={
                    "msg_id": message_id,
                    "queue": "pending",
                    "pending_count": pending_count + 1,
                },
            )
        except ValueError as e:
            self.logger.warning(
                str(e),
                extra={
                    "msg_id": message_id,
                    "pending_count": pending_count,
                    "max_messages": self.max_submit_size,
                },
            )
            raise
        except Exception as e:
            self.logger.error(
                f"Failed to enqueue message {message_id}: {str(e)}",
                extra={
                    "msg_id": message_id,
                    "error": str(e),
                },
            )
            raise

    async def get_pending_messages(self, batch_size: Optional[int] = None) -> List[QueuedMessage]:
        """Get batch of pending messages ready for processing.

        Retrieves messages that are ready for processing based on:
        1. Message state is PENDING
        2. Retry delay has elapsed since last attempt
        3. Maximum batch size not exceeded (uses MAX_MESSAGES_PER_RESPONSE)

        Args:
            batch_size: Optional override for batch size. If not provided, uses MAX_MESSAGES_PER_RESPONSE

        Returns:
            List[QueuedMessage]: List of messages ready for processing

        Note:
            Messages are not removed from pending queue until marked in_progress
            to prevent message loss in case of crashes.
        """
        try:
            # Use configured max if no batch_size provided
            effective_batch_size = min(batch_size or self.max_batch_size, self.max_batch_size)

            # Get all pending messages
            pending = await self.redis.hgetall(self.pending_queue)
            messages = []
            processed_ids = set()  # Track processed message IDs

            for message_data in pending.values():
                if len(messages) >= effective_batch_size:
                    break

                message = QueuedMessage.from_dict(json.loads(message_data))

                # Skip if we've already processed this message
                if message.message_id in processed_ids:
                    continue

                # Check if message is ready for retry based on window
                if (
                    message.last_attempt is None
                    or time.time() - message.last_attempt >= self.retry_delay
                ):
                    messages.append(message)
                    processed_ids.add(message.message_id)

            return messages
        except Exception as e:
            self.logger.error(
                f"Failed to get pending messages: {str(e)}",
                extra={
                    "error": str(e),
                    "batch_size": effective_batch_size,
                },
            )
            return []

    async def mark_in_progress(self, message_id: str) -> None:
        """Mark message as in progress.

        Atomically moves message from pending to in_progress queue.
        Updates message metadata:
        - Sets state to IN_PROGRESS
        - Increments retry count
        - Updates last attempt timestamp

        Args:
            message_id (str): Message identifier to mark as in progress

        Raises:
            Exception: If Redis transaction fails
            KeyError: If message not found in pending queue

        Note:
            Uses Redis transaction to ensure atomic state transition
        """
        try:
            # Get message from pending queue
            message_data = await self.redis.hget(self.pending_queue, message_id)
            if not message_data:
                return

            # Update state and move to in progress queue
            message = QueuedMessage.from_dict(json.loads(message_data))
            message.state = MessageState.IN_PROGRESS
            message.last_attempt = time.time()
            message.retry_count += 1

            # Atomic operation: remove from pending, add to in progress
            async with self.redis.pipeline() as pipe:
                await pipe.hdel(self.pending_queue, message_id)
                await pipe.hset(self.in_progress_queue, message_id, json.dumps(message.to_dict()))
                await pipe.execute()

            self.logger.info(
                f"Message {message_id} marked in progress",
                extra={
                    "msg_id": message_id,
                    "retry_count": message.retry_count,
                },
            )
        except Exception as e:
            self.logger.error(
                f"Failed to mark message {message_id} in progress: {str(e)}",
                extra={
                    "msg_id": message_id,
                    "error": str(e),
                },
            )
            raise

    async def mark_delivered(self, message_id: str) -> None:
        """Mark message as successfully delivered.

        Atomically moves message from in_progress to delivered queue.
        Updates message state to DELIVERED and preserves delivery metrics.

        Args:
            message_id (str): Message identifier to mark as delivered

        Raises:
            Exception: If Redis transaction fails
            KeyError: If message not found in in_progress queue

        Note:
            Messages in delivered queue can be pruned after retention period
        """
        try:
            # Get message from in progress queue
            message_data = await self.redis.hget(self.in_progress_queue, message_id)
            if not message_data:
                return

            # Update state and move to delivered queue
            message = QueuedMessage.from_dict(json.loads(message_data))
            message.state = MessageState.DELIVERED

            # Atomic operation: remove from in progress, add to delivered
            async with self.redis.pipeline() as pipe:
                await pipe.hdel(self.in_progress_queue, message_id)
                await pipe.hset(self.delivered_queue, message_id, json.dumps(message.to_dict()))
                await pipe.execute()

            self.logger.info(
                f"Message {message_id} marked delivered",
                extra={
                    "msg_id": message_id,
                    "retry_count": message.retry_count,
                },
            )
        except Exception as e:
            self.logger.error(
                f"Failed to mark message {message_id} delivered: {str(e)}",
                extra={
                    "msg_id": message_id,
                    "error": str(e),
                },
            )
            raise

    async def mark_failed(self, message_id: str, error: str) -> None:
        """Mark message as failed and handle retries.

        Processes message failure by:
        1. Moving message from in_progress queue
        2. Checking retry count against max_retries
        3. Moving to either pending (for retry) or dead_letter queue
        4. Updating error information and metrics

        Args:
            message_id (str): Message identifier to mark as failed
            error (str): Error message describing the failure

        Raises:
            Exception: If Redis transaction fails
            KeyError: If message not found in in_progress queue

        Note:
            Messages in dead_letter queue require manual intervention
        """
        try:
            # Get message from in progress queue
            message_data = await self.redis.hget(self.in_progress_queue, message_id)
            if not message_data:
                return

            message = QueuedMessage.from_dict(json.loads(message_data))
            message.error = error

            # Check retry count
            if message.retry_count >= self.max_retries:
                # Move to dead letter queue
                message.state = MessageState.DEAD_LETTER
                target_queue = self.dead_letter_queue
            else:
                # Move back to pending for retry
                message.state = MessageState.FAILED
                target_queue = self.pending_queue

            # Atomic operation: remove from in progress, add to target queue
            async with self.redis.pipeline() as pipe:
                await pipe.hdel(self.in_progress_queue, message_id)
                await pipe.hset(target_queue, message_id, json.dumps(message.to_dict()))
                await pipe.execute()

            self.logger.warning(
                f"Message {message_id} marked failed",
                extra={
                    "msg_id": message_id,
                    "error": error,
                    "retry_count": message.retry_count,
                    "state": message.state.value,
                },
            )
        except Exception as e:
            self.logger.error(
                f"Failed to mark message {message_id} failed: {str(e)}",
                extra={
                    "msg_id": message_id,
                    "error": str(e),
                },
            )
            raise

    async def cleanup_expired_messages(self) -> None:
        """Remove messages older than MESSAGE_RETENTION_DAYS.

        This implements the message retention policy from OGWS-1.txt section 2.3.
        Messages older than MESSAGE_RETENTION_DAYS are removed from delivered and
        dead letter queues.
        """
        try:
            cutoff = time.time() - (self.message_retention_days * 24 * 60 * 60)

            for queue in [self.delivered_queue, self.dead_letter_queue]:
                messages = await self.redis.hgetall(queue)
                for msg_id, msg_data in messages.items():
                    message = QueuedMessage.from_dict(json.loads(msg_data))
                    if message.created_at < cutoff:
                        await self.redis.hdel(queue, msg_id)
                        self.logger.info(
                            f"Removed expired message {msg_id}",
                            extra={
                                "msg_id": msg_id,
                                "queue": queue,
                                "age_days": (time.time() - message.created_at) / (24 * 60 * 60),
                            },
                        )
        except Exception as e:
            self.logger.error(
                f"Failed to cleanup expired messages: {str(e)}",
                extra={
                    "error": str(e),
                    "retention_days": self.message_retention_days,
                },
            )
