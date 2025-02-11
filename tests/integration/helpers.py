"""Helper utilities for integration testing.

This module provides common utilities and helper functions for:
- Service state management
- Test data generation
- Assertion helpers
- Cleanup utilities
"""

from typing import Any, Dict, List, Optional

import aioredis
import boto3
from prometheus_client.parser import text_string_to_metric_families


class RedisHelper:
    """Helper class for Redis operations during testing."""

    def __init__(self, client: aioredis.Redis):
        self.client = client

    async def set_message_state(self, message_id: str, state: Dict[str, Any]):
        """Set message state in Redis."""
        await self.client.hset(f"message:{message_id}", mapping=state)

    async def get_message_state(self, message_id: str) -> Optional[Dict[str, Any]]:
        """Get message state from Redis."""
        state = await self.client.hgetall(f"message:{message_id}")
        return state if state else None

    async def clear_message_states(self, pattern: str = "message:*"):
        """Clear all message states matching pattern."""
        keys = await self.client.keys(pattern)
        if keys:
            await self.client.delete(*keys)


class DynamoDBHelper:
    """Helper class for DynamoDB operations during testing."""

    def __init__(self, client: boto3.client):
        self.client = client

    def create_test_table(self, table_name: str):
        """Create a test table in DynamoDB."""
        try:
            self.client.create_table(
                TableName=table_name,
                KeySchema=[
                    {"AttributeName": "id", "KeyType": "HASH"},
                    {"AttributeName": "timestamp", "KeyType": "RANGE"},
                ],
                AttributeDefinitions=[
                    {"AttributeName": "id", "AttributeType": "S"},
                    {"AttributeName": "timestamp", "AttributeType": "N"},
                ],
                BillingMode="PAY_PER_REQUEST",
            )
        except self.client.exceptions.ResourceInUseException:
            pass  # Table already exists

    def delete_test_table(self, table_name: str):
        """Delete a test table from DynamoDB."""
        try:
            self.client.delete_table(TableName=table_name)
        except self.client.exceptions.ResourceNotFoundException:
            pass  # Table doesn't exist


class MetricsHelper:
    """Helper class for metrics verification during testing."""

    @staticmethod
    def get_metric_value(metrics_data: str, metric_name: str) -> Optional[float]:
        """Extract a specific metric value from metrics data."""
        for family in text_string_to_metric_families(metrics_data):
            if family.name == metric_name:
                return family.samples[0].value
        return None

    @staticmethod
    def assert_metric_present(metrics_data: str, metric_name: str):
        """Assert that a specific metric is present in metrics data."""
        value = MetricsHelper.get_metric_value(metrics_data, metric_name)
        assert value is not None, f"Metric {metric_name} not found in metrics data"

    @staticmethod
    def assert_metric_value(metrics_data: str, metric_name: str, expected_value: float):
        """Assert that a specific metric has the expected value."""
        value = MetricsHelper.get_metric_value(metrics_data, metric_name)
        assert (
            value == expected_value
        ), f"Metric {metric_name} has value {value}, expected {expected_value}"


class MessageHelper:
    """Helper class for message generation and validation during testing."""

    @staticmethod
    def create_test_message(message_type: str, **kwargs) -> Dict[str, Any]:
        """Create a test message with specified parameters."""
        base_message = {
            "type": message_type,
            "timestamp": kwargs.get("timestamp", "2024-02-11T12:00:00Z"),
            "id": kwargs.get("id", "test_message_001"),
        }
        base_message.update(kwargs)
        return base_message

    @staticmethod
    def assert_message_format(message: Dict[str, Any], expected_fields: List[str]):
        """Assert that a message contains all expected fields."""
        for field in expected_fields:
            assert field in message, f"Expected field '{field}' not found in message"

    @staticmethod
    def assert_message_state(message: Dict[str, Any], expected_state: str):
        """Assert that a message is in the expected state."""
        assert (
            message.get("state") == expected_state
        ), f"Message in state {message.get('state')}, expected {expected_state}"


async def setup_test_environment(
    redis_client: aioredis.Redis, dynamodb_client: boto3.client, table_name: str
) -> tuple[RedisHelper, DynamoDBHelper]:
    """Set up a clean test environment with required services."""
    redis_helper = RedisHelper(redis_client)
    dynamodb_helper = DynamoDBHelper(dynamodb_client)

    # Clear Redis test database
    await redis_client.flushdb()

    # Set up DynamoDB test table
    dynamodb_helper.create_test_table(table_name)

    return redis_helper, dynamodb_helper


async def cleanup_test_environment(
    redis_client: aioredis.Redis, dynamodb_client: boto3.client, table_name: str
):
    """Clean up the test environment after tests."""
    # Clear Redis test database
    await redis_client.flushdb()

    # Remove DynamoDB test table
    DynamoDBHelper(dynamodb_client).delete_test_table(table_name)
