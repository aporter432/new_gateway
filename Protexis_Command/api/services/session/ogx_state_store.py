"""
This module provides a message state store that can be used to store the state of a message.

The message state store is used to store the state of a message in a persistent way.
It implements state management as defined in OGx-1.txt Section 5.3, supporting:
- State retrieval and history tracking
- Environment-specific storage (Redis/DynamoDB)
- Atomic state transitions
- Error handling and logging

Configuration Sources:
    - protocols.ogx.constants.message_states: State definitions
    - core.app_settings: Environment configuration
    - OGx-1.txt Section 5.3: State transition rules
    - protocols.ogx.encoding.json: JSON encoding/decoding

Environment Handling:
    Development (Redis):
        - Local state storage
        - Fast retrieval
        - Simplified setup
        - Development logging

    Production (DynamoDB):
        - Distributed state management
        - High availability
        - Audit logging
        - Production monitoring
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

import boto3

from Protexis_Command.api.config import MessageState
from Protexis_Command.api.encoding.json import (
    decode_metadata,
    decode_state,
    encode_metadata,
    encode_state,
)
from Protexis_Command.core.logging.log_settings import LoggingConfig
from Protexis_Command.core.logging.loggers import get_protocol_logger
from Protexis_Command.protocol.ogx.validation.ogx_validation_exceptions import (
    EncodingError,
    OGxProtocolError,
)


class MessageStateStore(ABC):
    """Abstract interface for message state storage."""

    @abstractmethod
    async def update_state(
        self, message_id: int, new_state: MessageState, metadata: Optional[Dict] = None
    ) -> None:
        """Update message state."""

    @abstractmethod
    async def get_state(self, message_id: int) -> Optional[Dict]:
        """Get current message state.

        Implements state retrieval as defined in OGx-1.txt Section 5.3.
        Returns the current state and metadata for a message.

        Args:
            message_id: ID of message to retrieve state for

        Returns:
            Optional[Dict]: Message state information if found:
                {
                    "state": MessageState value,
                    "timestamp": ISO format timestamp,
                    "metadata": Additional state metadata
                }
            None if message not found

        Raises:
            OGxProtocolError: If state retrieval fails
        """

    @abstractmethod
    async def get_state_history(self, message_id: int) -> List[Dict]:
        """Get state transition history for a message.

        Implements state history tracking as defined in OGx-1.txt Section 5.3.
        Returns the complete history of state transitions for audit and debugging.

        Args:
            message_id: ID of message to retrieve history for

        Returns:
            List[Dict]: List of historical states, ordered by timestamp (oldest first):
                [{
                    "state": MessageState value,
                    "timestamp": ISO format timestamp,
                    "metadata": Additional state metadata
                }, ...]
            Empty list if no history found

        Raises:
            OGxProtocolError: If history retrieval fails
        """


class RedisMessageStateStore(MessageStateStore):
    """Redis implementation for development."""

    def __init__(self, redis_client: Any) -> None:
        """Initialize Redis store."""
        self.redis = redis_client
        self.logger = get_protocol_logger(LoggingConfig())

    async def update_state(
        self, message_id: int, new_state: MessageState, metadata: Optional[Dict] = None
    ) -> None:
        """Update state in Redis."""
        key = f"OGx:messages:{message_id}"
        timestamp = datetime.utcnow().isoformat()

        try:
            # Get current state
            current = await self.redis.hgetall(f"{key}:state")

            if current:
                # Add to history using consistent encoding
                history_entry = {
                    "state": current["state"],
                    "timestamp": current["timestamp"],
                    "metadata": decode_metadata(current.get("metadata", "{}")),
                }
                await self.redis.rpush(f"{key}:history", encode_state(history_entry))

            # Update current state using consistent encoding
            await self.redis.hmset(
                f"{key}:state",
                {
                    "state": new_state.value,
                    "timestamp": timestamp,
                    "metadata": encode_metadata(metadata),
                },
            )

            self.logger.info(
                "Updated message %d state to %s",
                message_id,
                new_state.name,
                extra={
                    "message_id": message_id,
                    "new_state": new_state.name,
                    "timestamp": timestamp,
                    "component": "state_store",
                    "action": "update_state",
                },
            )

        except Exception as e:
            error_msg = f"Failed to update message {message_id} state: {str(e)}"
            self.logger.error(
                error_msg,
                extra={
                    "message_id": message_id,
                    "error": str(e),
                    "component": "state_store",
                    "action": "update_state",
                },
            )
            raise OGxProtocolError(error_msg) from e

    async def get_state(self, message_id: int) -> Optional[Dict]:
        """Get current message state from Redis."""
        key = f"OGx:messages:{message_id}"

        try:
            current = await self.redis.hgetall(f"{key}:state")

            if not current:
                return None

            return {
                "state": int(current["state"]),
                "timestamp": current["timestamp"],
                "metadata": decode_metadata(current.get("metadata", "{}")),
            }

        except Exception as e:
            error_msg = f"Failed to get message {message_id} state: {str(e)}"
            self.logger.error(
                error_msg,
                extra={
                    "message_id": message_id,
                    "error": str(e),
                    "component": "state_store",
                    "action": "get_state",
                },
            )
            raise OGxProtocolError(error_msg) from e

    async def get_state_history(self, message_id: int) -> List[Dict]:
        """Get state transition history from Redis."""
        key = f"OGx:messages:{message_id}"

        try:
            history_data = await self.redis.lrange(f"{key}:history", 0, -1)
            history = []

            for entry in history_data:
                try:
                    history.append(decode_state(entry))
                except EncodingError as e:
                    self.logger.warning(
                        "Failed to parse history entry for message %d",
                        message_id,
                        extra={
                            "message_id": message_id,
                            "error": str(e),
                            "entry": entry,
                            "component": "state_store",
                            "action": "get_state_history",
                        },
                    )
                    continue

            return history

        except Exception as e:
            error_msg = f"Failed to get message {message_id} state history: {str(e)}"
            self.logger.error(
                error_msg,
                extra={
                    "message_id": message_id,
                    "error": str(e),
                    "component": "state_store",
                    "action": "get_state_history",
                },
            )
            raise OGxProtocolError(error_msg) from e


class DynamoDBMessageStateStore(MessageStateStore):
    """AWS DynamoDB implementation for production."""

    def __init__(self, table_name: str) -> None:
        """Initialize DynamoDB store."""
        dynamodb = boto3.resource("dynamodb")
        self.table = dynamodb.Table(table_name)  # type: ignore
        self.logger = get_protocol_logger(LoggingConfig())

    async def update_state(
        self, message_id: int, new_state: MessageState, metadata: Optional[Dict] = None
    ) -> None:
        """Update state in DynamoDB."""
        timestamp = datetime.utcnow().isoformat()

        try:
            # Store metadata using consistent encoding
            encoded_metadata = encode_metadata(metadata)

            await self.table.update_item(
                Key={"message_id": str(message_id)},
                UpdateExpression=(
                    "SET current_state = :state, "
                    "last_updated = :ts, "
                    "metadata = :meta, "
                    "GSI1PK = :gsi1pk"
                ),
                ExpressionAttributeValues={
                    ":state": new_state.value,
                    ":ts": timestamp,
                    ":meta": encoded_metadata,
                    ":gsi1pk": f"state#{new_state.name}",
                },
            )

            self.logger.info(
                "Updated message %d state to %s",
                message_id,
                new_state.name,
                extra={
                    "message_id": message_id,
                    "new_state": new_state.name,
                    "timestamp": timestamp,
                    "component": "state_store",
                    "action": "update_state",
                },
            )

        except Exception as e:
            error_msg = f"Failed to update message {message_id} state: {str(e)}"
            self.logger.error(
                error_msg,
                extra={
                    "message_id": message_id,
                    "error": str(e),
                    "component": "state_store",
                    "action": "update_state",
                },
            )
            raise OGxProtocolError(error_msg) from e

    async def get_state(self, message_id: int) -> Optional[Dict]:
        """Get current message state from DynamoDB."""
        try:
            response = await self.table.get_item(
                Key={"message_id": str(message_id)}, ConsistentRead=True
            )

            item = response.get("Item")
            if not item:
                return None

            return {
                "state": int(item["current_state"]),
                "timestamp": item["last_updated"],
                "metadata": decode_metadata(item.get("metadata", "{}")),
            }

        except Exception as e:
            self.logger.error(
                "Failed to get message %d state",
                message_id,
                extra={
                    "message_id": message_id,
                    "error": str(e),
                    "component": "state_store",
                    "action": "get_state",
                },
            )
            raise OGxProtocolError(f"Failed to get message {message_id} state: {str(e)}") from e

    async def get_state_history(self, message_id: int) -> List[Dict]:
        """Get state transition history from DynamoDB."""
        try:
            response = await self.table.query(
                KeyConditionExpression="message_id = :mid",
                ExpressionAttributeValues={":mid": str(message_id)},
                ProjectionExpression="state_value, #ts, metadata",
                ExpressionAttributeNames={"#ts": "timestamp"},
                ConsistentRead=True,
                ScanIndexForward=True,
            )

            history = []
            for item in response.get("Items", []):
                try:
                    history.append(
                        {
                            "state": int(item["state_value"]),
                            "timestamp": item["timestamp"],
                            "metadata": decode_metadata(item.get("metadata", "{}")),
                        }
                    )
                except (ValueError, KeyError) as e:
                    self.logger.warning(
                        "Failed to parse history entry for message %d",
                        message_id,
                        extra={
                            "message_id": message_id,
                            "error": str(e),
                            "component": "state_store",
                            "action": "get_state_history",
                            "item": item,
                        },
                    )
                    continue

            return history

        except Exception as e:
            self.logger.error(
                "Failed to get message %d state history",
                message_id,
                extra={
                    "message_id": message_id,
                    "error": str(e),
                    "component": "state_store",
                    "action": "get_state_history",
                },
            )
            raise OGxProtocolError(
                f"Failed to get message {message_id} state history: {str(e)}"
            ) from e
