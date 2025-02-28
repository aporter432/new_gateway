"""Unit tests for message state store implementations.

This module tests the message state store functionality:
- State updates
- State retrieval
- State history tracking
- Error handling
- Redis and DynamoDB implementations
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from Protexis_Command.api.config import MessageState
from Protexis_Command.api.services.session.ogx_state_store import (
    DynamoDBMessageStateStore,
    RedisMessageStateStore,
)
from Protexis_Command.protocols.ogx.validation.ogx_validation_exceptions import OGxProtocolError


@pytest.fixture
def mock_redis_client():
    """Create a mock Redis client."""
    client = AsyncMock()
    client.hgetall = AsyncMock(return_value={})
    client.hmset = AsyncMock()
    client.rpush = AsyncMock()
    client.lrange = AsyncMock(return_value=[])
    return client


@pytest.fixture
def mock_dynamodb_table():
    """Create a mock DynamoDB table."""
    table = MagicMock()
    table.update_item = AsyncMock()
    table.get_item = AsyncMock(return_value={})
    table.query = AsyncMock(return_value={"Items": []})
    return table


@pytest.fixture
def redis_store(mock_redis_client):
    """Create a RedisMessageStateStore instance."""
    return RedisMessageStateStore(mock_redis_client)


@pytest.fixture
def dynamodb_store(mock_dynamodb_table):
    """Create a DynamoDBMessageStateStore instance."""
    with patch("boto3.resource") as mock_boto3:
        mock_boto3.return_value.Table.return_value = mock_dynamodb_table
        store = DynamoDBMessageStateStore("test_table")
        return store


class TestRedisMessageStateStore:
    """Test suite for Redis message state store implementation."""

    @pytest.mark.asyncio
    async def test_update_state_success(self, redis_store, mock_redis_client):
        """Test successful state update in Redis."""
        message_id = 123
        new_state = MessageState.RECEIVED
        metadata = {"key": "value"}

        await redis_store.update_state(message_id, new_state, metadata)

        # Verify Redis operations
        mock_redis_client.hgetall.assert_called_once()
        mock_redis_client.hmset.assert_called_once()

        # Verify state was stored correctly
        hmset_args = mock_redis_client.hmset.call_args[0]
        assert hmset_args[0] == f"OGx:messages:{message_id}:state"
        assert "state" in hmset_args[1]
        assert "timestamp" in hmset_args[1]
        assert "metadata" in hmset_args[1]

    @pytest.mark.asyncio
    async def test_update_state_error(self, redis_store, mock_redis_client):
        """Test error handling during state update in Redis."""
        mock_redis_client.hmset.side_effect = Exception("Redis error")

        with pytest.raises(OGxProtocolError) as exc_info:
            await redis_store.update_state(123, MessageState.RECEIVED)

        assert "Failed to update message" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_state_success(self, redis_store, mock_redis_client):
        """Test successful state retrieval from Redis."""
        message_id = 123
        state_data = {"state": "1", "timestamp": datetime.utcnow().isoformat(), "metadata": "{}"}
        mock_redis_client.hgetall.return_value = state_data

        result = await redis_store.get_state(message_id)

        assert result is not None
        assert result["state"] == 1
        assert "timestamp" in result
        assert "metadata" in result

    @pytest.mark.asyncio
    async def test_get_state_error(self, redis_store, mock_redis_client):
        """Test error handling during state retrieval from Redis."""
        mock_redis_client.hgetall.side_effect = Exception("Redis error")

        with pytest.raises(OGxProtocolError) as exc_info:
            await redis_store.get_state(123)

        assert "Failed to get message" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_state_not_found(self, redis_store, mock_redis_client):
        """Test state retrieval when message doesn't exist."""
        mock_redis_client.hgetall.return_value = {}

        result = await redis_store.get_state(123)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_state_history_success(self, redis_store, mock_redis_client):
        """Test successful state history retrieval from Redis."""
        message_id = 123
        history_entry = {"state": 1, "timestamp": datetime.utcnow().isoformat(), "metadata": {}}
        mock_redis_client.lrange.return_value = [str(history_entry)]

        result = await redis_store.get_state_history(message_id)

        assert isinstance(result, list)
        mock_redis_client.lrange.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_state_history_error(self, redis_store, mock_redis_client):
        """Test error handling during history retrieval from Redis."""
        mock_redis_client.lrange.side_effect = Exception("Redis error")

        with pytest.raises(OGxProtocolError) as exc_info:
            await redis_store.get_state_history(123)

        assert "Failed to get message" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_state_history_invalid_entry(self, redis_store, mock_redis_client):
        """Test handling of invalid history entries in Redis."""
        mock_redis_client.lrange.return_value = ["invalid_json"]

        result = await redis_store.get_state_history(123)

        assert isinstance(result, list)
        assert len(result) == 0


class TestDynamoDBMessageStateStore:
    """Test suite for DynamoDB message state store implementation."""

    @pytest.mark.asyncio
    async def test_update_state_success(self, dynamodb_store, mock_dynamodb_table):
        """Test successful state update in DynamoDB."""
        message_id = 123
        new_state = MessageState.RECEIVED
        metadata = {"key": "value"}

        await dynamodb_store.update_state(message_id, new_state, metadata)

        mock_dynamodb_table.update_item.assert_called_once()
        update_args = mock_dynamodb_table.update_item.call_args[1]
        assert update_args["Key"]["message_id"] == str(message_id)
        assert "UpdateExpression" in update_args
        assert "ExpressionAttributeValues" in update_args

    @pytest.mark.asyncio
    async def test_update_state_error(self, dynamodb_store, mock_dynamodb_table):
        """Test error handling during state update in DynamoDB."""
        mock_dynamodb_table.update_item.side_effect = Exception("DynamoDB error")

        with pytest.raises(OGxProtocolError) as exc_info:
            await dynamodb_store.update_state(123, MessageState.RECEIVED)

        assert "Failed to update message" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_state_success(self, dynamodb_store, mock_dynamodb_table):
        """Test successful state retrieval from DynamoDB."""
        message_id = 123
        mock_dynamodb_table.get_item.return_value = {
            "Item": {
                "current_state": "1",
                "last_updated": datetime.utcnow().isoformat(),
                "metadata": "{}",
            }
        }

        result = await dynamodb_store.get_state(message_id)

        assert result is not None
        assert result["state"] == 1
        assert "timestamp" in result
        assert "metadata" in result

    @pytest.mark.asyncio
    async def test_get_state_error(self, dynamodb_store, mock_dynamodb_table):
        """Test error handling during state retrieval from DynamoDB."""
        mock_dynamodb_table.get_item.side_effect = Exception("DynamoDB error")

        with pytest.raises(OGxProtocolError) as exc_info:
            await dynamodb_store.get_state(123)

        assert "Failed to get message" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_state_not_found(self, dynamodb_store, mock_dynamodb_table):
        """Test state retrieval when message doesn't exist."""
        mock_dynamodb_table.get_item.return_value = {}

        result = await dynamodb_store.get_state(123)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_state_history_success(self, dynamodb_store, mock_dynamodb_table):
        """Test successful state history retrieval from DynamoDB."""
        message_id = 123
        history_item = {
            "state_value": "1",
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": "{}",
        }
        mock_dynamodb_table.query.return_value = {"Items": [history_item]}

        result = await dynamodb_store.get_state_history(message_id)

        assert isinstance(result, list)
        mock_dynamodb_table.query.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_state_history_error(self, dynamodb_store, mock_dynamodb_table):
        """Test error handling during history retrieval from DynamoDB."""
        mock_dynamodb_table.query.side_effect = Exception("DynamoDB error")

        with pytest.raises(OGxProtocolError) as exc_info:
            await dynamodb_store.get_state_history(123)

        assert "Failed to get message" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_state_history_invalid_entry(self, dynamodb_store, mock_dynamodb_table):
        """Test handling of invalid history entries in DynamoDB."""
        mock_dynamodb_table.query.return_value = {
            "Items": [{"state_value": "invalid", "timestamp": "invalid"}]
        }

        result = await dynamodb_store.get_state_history(123)

        assert isinstance(result, list)
        assert len(result) == 0
