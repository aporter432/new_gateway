"""
This module provides a message state store that can be used to store the state of a message.

The message state store is used to store the state of a message in a persistent way.

The message state store is used to store the state of a message in a persistent way.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional

from core.logging.loggers import get_protocol_logger
from protocols.ogx.constants import MessageState


class MessageStateStore(ABC):
    """Abstract interface for message state storage."""
    
    @abstractmethod
    async def update_state(
        self, 
        message_id: int, 
        new_state: MessageState,
        metadata: Optional[Dict] = None
    ) -> None:
        """Update message state."""
        pass

    @abstractmethod
    async def get_state(self, message_id: int) -> Optional[Dict]:
        """Get current message state."""
        pass

    @abstractmethod
    async def get_state_history(self, message_id: int) -> List[Dict]:
        """Get state transition history."""
        pass

class RedisMessageStateStore(MessageStateStore):
    """Redis implementation for development."""
    
    def __init__(self, redis_client) -> None:
        self.redis = redis_client
        self.logger = get_protocol_logger("state_store")

    async def update_state(
        self, 
        message_id: int, 
        new_state: MessageState,
        metadata: Optional[Dict] = None
    ) -> None:
        """Update state in Redis."""
        key = f"ogws:messages:{message_id}"
        timestamp = datetime.utcnow().isoformat()
        
        try:
            # Get current state
            current = await self.redis.hgetall(f"{key}:state")
            
            if current:
                # Add to history
                await self.redis.rpush(
                    f"{key}:history",
                    json.dumps({
                        "state": current["state"],
                        "timestamp": current["timestamp"],
                        "metadata": current.get("metadata", {})
                    })
                )
            
            # Update current state
            await self.redis.hmset(
                f"{key}:state",
                {
                    "state": new_state.value,
                    "timestamp": timestamp,
                    "metadata": json.dumps(metadata or {})
                }
            )
            
            self.logger.info(
                f"Updated message {message_id} state to {new_state.name}",
                extra={
                    "message_id": message_id,
                    "new_state": new_state.name,
                    "timestamp": timestamp
                }
            )
            
        except Exception as e:
            self.logger.error(
                f"Failed to update message {message_id} state: {str(e)}",
                extra={
                    "message_id": message_id,
                    "error": str(e)
                }
            )
            raise

class DynamoDBMessageStateStore(MessageStateStore):
    """AWS DynamoDB implementation for production."""
    
    def __init__(self, table_name: str) -> None:
        self.table = boto3.resource('dynamodb').Table(table_name)
        self.logger = get_protocol_logger("state_store")

    async def update_state(
        self, 
        message_id: int, 
        new_state: MessageState,
        metadata: Optional[Dict] = None
    ) -> None:
        """Update state in DynamoDB."""
        timestamp = datetime.utcnow().isoformat()
        
        try:
            await self.table.update_item(
                Key={'message_id': str(message_id)},
                UpdateExpression=(
                    "SET current_state = :state, "
                    "last_updated = :ts, "
                    "metadata = :meta, "
                    "GSI1PK = :gsi1pk"
                ),
                ExpressionAttributeValues={
                    ':state': new_state.value,
                    ':ts': timestamp,
                    ':meta': metadata or {},
                    ':gsi1pk': f"state#{new_state.name}"
                }
            )
            
            self.logger.info(
                f"Updated message {message_id} state to {new_state.name}",
                extra={
                    "message_id": message_id,
                    "new_state": new_state.name,
                    "timestamp": timestamp
                }
            )
            
        except Exception as e:
            self.logger.error(
                f"Failed to update message {message_id} state: {str(e)}",
                extra={
                    "message_id": message_id,
                    "error": str(e)
                }
            )
            raise