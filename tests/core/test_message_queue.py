"""Test suite for message queue implementation.

This module provides comprehensive testing of the message queue functionality:
1. Message lifecycle (enqueue -> in_progress -> delivered)
2. Retry mechanism and backoff
3. Dead letter queue handling
4. Error scenarios and recovery
5. Batch processing
"""

import json
import pytest
import time
from typing import Dict, Optional
from unittest.mock import AsyncMock, MagicMock, patch

from redis.asyncio import Redis
from core.app_settings import Settings
from core.message_queue import MessageQueue, MessageState, QueuedMessage


@pytest.fixture
def settings():
    """Test settings fixture."""
    return Settings(
        OGWS_CLIENT_ID="test_client",
        OGWS_CLIENT_SECRET="test_secret",
        CUSTOMER_ID="test_customer",
    )


@pytest.fixture
async def mock_redis():
    """Mock Redis client fixture."""
    redis = AsyncMock(spec=Redis)
    redis.hset = AsyncMock()
    redis.hget = AsyncMock()
    redis.hdel = AsyncMock()
    redis.hgetall = AsyncMock(return_value={})
    redis.pipeline = MagicMock()

    # Mock pipeline context manager
    pipeline = AsyncMock()
    pipeline.hdel = AsyncMock()
    pipeline.hset = AsyncMock()
    pipeline.execute = AsyncMock()
    redis.pipeline.return_value.__aenter__.return_value = pipeline
    redis.pipeline.return_value.__aexit__ = AsyncMock()

    return redis


@pytest.fixture
async def queue(settings, mock_redis):
    """Message queue fixture."""
    return MessageQueue(mock_redis, settings)


@pytest.mark.asyncio
async def test_enqueue_message(queue, mock_redis):
    """Test enqueueing a new message."""
    message_id = "test_msg_1"
    payload = {"test": "data"}

    await queue.enqueue_message(message_id, payload)

    # Verify Redis call
    mock_redis.hset.assert_called_once()
    args = mock_redis.hset.call_args[0]
    assert args[0] == queue.pending_queue
    assert args[1] == message_id

    # Verify stored message
    stored_msg = json.loads(args[2])
    assert stored_msg["message_id"] == message_id
    assert stored_msg["payload"] == payload
    assert stored_msg["state"] == MessageState.PENDING.value
    assert stored_msg["retry_count"] == 0


@pytest.mark.asyncio
async def test_get_pending_messages(queue, mock_redis):
    """Test retrieving pending messages."""
    # Setup mock data
    messages = {
        "msg1": json.dumps(QueuedMessage("msg1", {"data": "1"}).to_dict()),
        "msg2": json.dumps(QueuedMessage("msg2", {"data": "2"}).to_dict()),
    }
    mock_redis.hgetall.return_value = messages

    # Get messages
    result = await queue.get_pending_messages(batch_size=2)

    # Verify results
    assert len(result) == 2
    assert all(isinstance(msg, QueuedMessage) for msg in result)
    assert result[0].message_id == "msg1"
    assert result[1].message_id == "msg2"


@pytest.mark.asyncio
async def test_message_lifecycle(queue, mock_redis):
    """Test complete message lifecycle."""
    message_id = "lifecycle_test"
    payload = {"test": "lifecycle"}

    # 1. Enqueue message
    await queue.enqueue_message(message_id, payload)

    # 2. Setup mock for retrieving message
    stored_message = QueuedMessage(message_id, payload)
    mock_redis.hget.return_value = json.dumps(stored_message.to_dict())

    # 3. Mark in progress
    await queue.mark_in_progress(message_id)

    # Verify moved to in_progress
    pipeline = mock_redis.pipeline.return_value.__aenter__.return_value
    assert pipeline.hdel.call_args[0][0] == queue.pending_queue
    assert pipeline.hset.call_args[0][0] == queue.in_progress_queue

    # 4. Mark delivered
    await queue.mark_delivered(message_id)

    # Verify moved to delivered
    pipeline = mock_redis.pipeline.return_value.__aenter__.return_value
    assert pipeline.hdel.call_args[0][0] == queue.in_progress_queue
    assert pipeline.hset.call_args[0][0] == queue.delivered_queue


@pytest.mark.asyncio
async def test_retry_mechanism(queue, mock_redis):
    """Test message retry mechanism."""
    message_id = "retry_test"
    error_msg = "Test failure"

    # Setup mock message in in_progress
    message = QueuedMessage(message_id, {"test": "retry"}, retry_count=1)
    mock_redis.hget.return_value = json.dumps(message.to_dict())

    # Mark failed (should go back to pending)
    await queue.mark_failed(message_id, error_msg)

    # Verify moved back to pending
    pipeline = mock_redis.pipeline.return_value.__aenter__.return_value
    assert pipeline.hdel.call_args[0][0] == queue.in_progress_queue
    stored_msg = json.loads(pipeline.hset.call_args[0][2])
    assert stored_msg["state"] == MessageState.FAILED.value
    assert stored_msg["error"] == error_msg
    assert stored_msg["retry_count"] == 1


@pytest.mark.asyncio
async def test_dead_letter_queue(queue, mock_redis):
    """Test dead letter queue handling."""
    message_id = "dlq_test"

    # Setup mock message that exceeded retries
    message = QueuedMessage(message_id, {"test": "dlq"}, retry_count=queue.max_retries)
    mock_redis.hget.return_value = json.dumps(message.to_dict())

    # Mark failed (should go to DLQ)
    await queue.mark_failed(message_id, "Final failure")

    # Verify moved to dead letter queue
    pipeline = mock_redis.pipeline.return_value.__aenter__.return_value
    assert pipeline.hdel.call_args[0][0] == queue.in_progress_queue
    assert pipeline.hset.call_args[0][0] == queue.dead_letter_queue


@pytest.mark.asyncio
async def test_error_handling(queue, mock_redis):
    """Test error handling in queue operations."""
    message_id = "error_test"

    # Simulate Redis error
    mock_redis.hset.side_effect = Exception("Redis connection failed")

    # Verify error is propagated
    with pytest.raises(Exception):
        await queue.enqueue_message(message_id, {"test": "error"})


@pytest.mark.asyncio
async def test_batch_processing(queue, mock_redis):
    """Test batch message processing."""
    # Setup mock data for 15 messages
    messages = {
        f"msg{i}": json.dumps(QueuedMessage(f"msg{i}", {"data": str(i)}).to_dict())
        for i in range(15)
    }
    mock_redis.hgetall.return_value = messages

    # Get first batch
    batch1 = await queue.get_pending_messages(batch_size=5)
    assert len(batch1) == 5
    batch1_ids = {msg.message_id for msg in batch1}

    # Reset mock data to simulate fresh Redis state
    mock_redis.hgetall.return_value = {k: v for k, v in messages.items() if k not in batch1_ids}

    # Get second batch
    batch2 = await queue.get_pending_messages(batch_size=10)
    assert len(batch2) == 10

    # Verify no duplicates
    message_ids = {msg.message_id for msg in batch1 + batch2}
    assert len(message_ids) == len(batch1) + len(batch2)

    # Verify we got different messages each time
    batch2_ids = {msg.message_id for msg in batch2}
    assert not batch1_ids.intersection(batch2_ids)
