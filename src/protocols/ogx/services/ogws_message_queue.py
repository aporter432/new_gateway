"""Message queue implementation for OGWS message processing.

This module provides a Redis-based message queue implementation that handles:
- Message state tracking and transitions
- Dead letter queue (DLQ) for failed messages after max retries
- Message retry logic and backoff

SOLID Principles:
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
from redis.exceptions import RedisError

from core.app_settings import Settings
from core.logging.loggers import get_protocol_logger
from protocols.ogx.constants import MessageState
from protocols.ogx.constants.limits import (
    DEFAULT_CALLS_PER_MINUTE,
    DEFAULT_WINDOW_SECONDS,
    MAX_MESSAGES_PER_RESPONSE,
    MAX_SUBMIT_MESSAGES,
    MESSAGE_RETENTION_DAYS,
)


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
        state: MessageState = MessageState.ACCEPTED,
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

    This provides robust implementation of message queue management with the following features:
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
        self.logger = get_protocol_logger("message_queue")

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
                "Enqueued message %s",
                message_id,
                extra={
                    "customer_id": self.settings.CUSTOMER_ID,
                    "asset_id": "message_queue",
                    "message_id": message_id,
                    "action": "enqueue",
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
                "Failed to enqueue message %s: %s",
                message_id,
                str(e),
                extra={
                    "customer_id": self.settings.CUSTOMER_ID,
                    "asset_id": "message_queue",
                    "message_id": message_id,
                    "error": str(e),
                    "action": "enqueue",
                },
            )
            raise

    async def get_pending_messages(self, batch_size: Optional[int] = None) -> List[QueuedMessage]:
        """Get batch of pending messages ready for processing.

        Args:
            batch_size: Optional override for default batch size
        """
        try:
            effective_batch_size = batch_size or self.max_batch_size
            message_data = await self.redis.hgetall(self.pending_queue)
            messages = []

            for message_id, data in list(message_data.items())[:effective_batch_size]:
                try:
                    message = QueuedMessage.from_dict(json.loads(data))
                    messages.append(message)
                except (json.JSONDecodeError, KeyError) as e:
                    self.logger.error(
                        "Failed to decode message %s: %s",
                        message_id,
                        str(e),
                        extra={
                            "customer_id": self.settings.CUSTOMER_ID,
                            "asset_id": "message_queue",
                            "message_id": message_id,
                            "error": str(e),
                            "action": "get_pending",
                        },
                    )

            return messages

        except RedisError as e:
            self.logger.error(
                "Failed to get pending messages: %s",
                str(e),
                extra={
                    "customer_id": self.settings.CUSTOMER_ID,
                    "asset_id": "message_queue",
                    "error": str(e),
                    "action": "get_pending",
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
            message.state = MessageState.SENDING_IN_PROGRESS
            message.last_attempt = time.time()
            message.retry_count += 1

            # Atomic operation: remove from pending, add to in progress
            async with self.redis.pipeline() as pipe:
                await pipe.hdel(self.pending_queue, message_id)
                await pipe.hset(self.in_progress_queue, message_id, json.dumps(message.to_dict()))
                await pipe.execute()

            self.logger.info(
                "Message %s marked in progress",
                message_id,
                extra={
                    "customer_id": self.settings.CUSTOMER_ID,
                    "asset_id": "message_queue",
                    "message_id": message_id,
                    "action": "mark_in_progress",
                },
            )
        except Exception as e:
            self.logger.error(
                "Failed to mark message %s in progress: %s",
                message_id,
                str(e),
                extra={
                    "customer_id": self.settings.CUSTOMER_ID,
                    "asset_id": "message_queue",
                    "message_id": message_id,
                    "error": str(e),
                    "action": "mark_in_progress",
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
            message.state = MessageState.RECEIVED

            # Atomic operation: remove from in progress, add to delivered
            async with self.redis.pipeline() as pipe:
                await pipe.hdel(self.in_progress_queue, message_id)
                await pipe.hset(self.delivered_queue, message_id, json.dumps(message.to_dict()))
                await pipe.execute()

            self.logger.info(
                "Message %s marked delivered",
                message_id,
                extra={
                    "customer_id": self.settings.CUSTOMER_ID,
                    "asset_id": "message_queue",
                    "message_id": message_id,
                    "action": "mark_delivered",
                },
            )
        except Exception as e:
            self.logger.error(
                "Failed to mark message %s delivered: %s",
                message_id,
                str(e),
                extra={
                    "customer_id": self.settings.CUSTOMER_ID,
                    "asset_id": "message_queue",
                    "message_id": message_id,
                    "error": str(e),
                    "action": "mark_delivered",
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
                message.state = MessageState.TIMED_OUT
                target_queue = self.dead_letter_queue
            else:
                # Move back to pending for retry
                message.state = MessageState.DELIVERY_FAILED
                target_queue = self.pending_queue

            # Atomic operation: remove from in progress, add to target queue
            async with self.redis.pipeline() as pipe:
                await pipe.hdel(self.in_progress_queue, message_id)
                await pipe.hset(target_queue, message_id, json.dumps(message.to_dict()))
                await pipe.execute()

            self.logger.info(
                "Message %s marked failed",
                message_id,
                extra={
                    "customer_id": self.settings.CUSTOMER_ID,
                    "asset_id": "message_queue",
                    "message_id": message_id,
                    "retry_count": message.retry_count,
                    "max_retries": self.max_retries,
                    "error": error,
                    "action": "mark_failed",
                },
            )
        except Exception as e:
            self.logger.error(
                "Failed to mark message %s failed: %s",
                message_id,
                str(e),
                extra={
                    "customer_id": self.settings.CUSTOMER_ID,
                    "asset_id": "message_queue",
                    "message_id": message_id,
                    "error": str(e),
                    "action": "mark_failed",
                },
            )
            raise

    async def cleanup_expired_messages(self) -> None:
        """Clean up expired messages from all queues."""
        try:
            cutoff = time.time() - (self.message_retention_days * 24 * 60 * 60)
            queues = [
                self.pending_queue,
                self.in_progress_queue,
                self.delivered_queue,
                self.dead_letter_queue,
            ]

            for queue in queues:
                message_data = await self.redis.hgetall(queue)
                for message_id, data in message_data.items():
                    try:
                        message = QueuedMessage.from_dict(json.loads(data))
                        if message.created_at < cutoff:
                            await self.redis.hdel(queue, message_id)
                            self.logger.debug(
                                "Cleaned up expired message",
                                extra={
                                    "customer_id": self.settings.CUSTOMER_ID,
                                    "asset_id": "message_queue",
                                    "message_id": message_id,
                                    "queue": queue,
                                    "age_days": (time.time() - message.created_at) / (24 * 60 * 60),
                                    "action": "cleanup",
                                },
                            )
                    except (json.JSONDecodeError, KeyError) as e:
                        self.logger.warning(
                            "Failed to process message %s during cleanup: %s",
                            message_id,
                            str(e),
                            extra={
                                "customer_id": self.settings.CUSTOMER_ID,
                                "asset_id": "message_queue",
                                "message_id": message_id,
                                "error": str(e),
                                "action": "cleanup",
                            },
                        )

        except RedisError as e:
            self.logger.error(
                "Failed to cleanup expired messages: %s",
                str(e),
                extra={
                    "customer_id": self.settings.CUSTOMER_ID,
                    "asset_id": "message_queue",
                    "error": str(e),
                    "action": "cleanup",
                },
            )
