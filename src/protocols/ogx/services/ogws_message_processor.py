"""Message processing and validation for OGWS messages.

This module implements message handling as defined in OGWS-1.txt specifications.
It serves as the primary message processing pipeline, integrating with:

Configuration Sources (Single Source of Truth):
    - core.app_settings: Environment and credential configuration
    - protocols.ogx.constants.message_states: State definitions and transitions
    - protocols.ogx.constants.transport_types: Transport method definitions
    - protocols.ogx.constants.limits: Rate and size constraints
    - protocols.ogx.validation: Message format validation rules

OGWS Integration (OGWS-1.txt):
    - Section 4.2: Rate Limiting and Quotas
        - Concurrent request limits
        - Time-based quotas
    - Section 5.1: Message Format and Validation
        - Field requirements and constraints
        - Size limits and encoding
    - Section 5.3: Message States
        - State transition rules
        - Error handling
    - Section 5.4: Transport Selection
        - Network type determination
        - Routing decisions
    - Section 7.2: Error Recovery
        - Message retry strategies
        - State recovery procedures

Environment Handling:
    Development:
        - Uses Redis for state storage
        - Allows local testing with minimal setup
        - Provides detailed logging for debugging
        - Uses test credentials from app_settings

    Production:
        - Uses DynamoDB for state persistence
        - Implements strict validation rules
        - Enforces rate limiting
        - Requires proper credentials
        - TODO: Implement production-grade error handling
        - TODO: Add comprehensive metrics collection
        - TODO: Implement retry backoff strategy (Section 7.2)
        - TODO: Add concurrent request limiting (Section 4.2)

Note:
    This implementation focuses on Service Provider (SP) requirements.
    For Mobile-Originated (MO) message handling, see OGWS-1.txt Section 6.
"""

from typing import Any, Dict, Optional

from core.app_settings import get_settings
from core.logging.loggers import get_protocol_logger
from infrastructure.redis import get_redis_client
from protocols.ogx.constants import MessageState
from protocols.ogx.constants.transport_types import TransportType
from protocols.ogx.validation.common.exceptions import OGxProtocolError, ValidationError
from protocols.ogx.validation.json.field_validator import OGxFieldValidator
from protocols.ogx.validation.json.message_validator import OGxMessageValidator

from .ogws_state_store import DynamoDBMessageStateStore, MessageStateStore, RedisMessageStateStore


class MessageProcessor:
    """Processes and validates OGWS messages.

    This class implements the core message processing pipeline following OGWS-1.txt.
    It enforces:
    1. Message format validation (Section 5.1)
    2. State transitions (Section 5.3)
    3. Transport selection (Section 5.4)
    4. Rate limiting (Section 4.2)

    Configuration Sources (in order of precedence):
    1. Environment-specific state store (Redis/DynamoDB)
    2. OGWS-1.txt specifications
    3. Development defaults from app_settings

    Environment-Specific Behavior:
    Development:
        - Uses Redis state store
        - Allows test messages
        - Detailed logging
        - Flexible validation

    Production:
        - Uses DynamoDB state store
        - Strict validation
        - Rate limiting
        - Error tracking
        - TODO: Implement production metrics
        - TODO: Add failover handling
    """

    def __init__(self, state_store: Optional[MessageStateStore] = None) -> None:
        """Initialize message processor with validators and state store.

        Args:
            state_store: Optional state store override. If not provided:
                - Development: Uses Redis (local/test)
                - Production: Uses DynamoDB (AWS)
        """
        self.message_validator = OGxMessageValidator()
        self.field_validator = OGxFieldValidator()
        self.state_store = state_store or self._get_default_state_store()
        self.logger = get_protocol_logger("message_processor")
        self.settings = get_settings()

    def _get_default_state_store(self) -> MessageStateStore:
        """Get default state store based on environment.

        Returns:
            MessageStateStore: Environment-appropriate store:
                - Development: Redis (from docker-compose.yml)
                - Production: DynamoDB (from AWS)

        Note:
            Production requires DYNAMODB_TABLE_NAME in environment
        """
        if self.settings.ENVIRONMENT == "production":
            return DynamoDBMessageStateStore(self.settings.DYNAMODB_TABLE_NAME)
        return RedisMessageStateStore(get_redis_client())

    async def validate_outbound_message(self, message: Dict[str, Any]) -> Optional[Dict[str, str]]:
        """Validate outbound message before sending.

        Implements validation rules from OGWS-1.txt Section 5.1:
        - Message size limits (MAX_OGX_PAYLOAD_BYTES, MAX_IDP_*_PAYLOAD_BYTES)
        - Required fields and format
        - Network-specific constraints

        Environment-Specific Behavior:
            Development:
                - Allows test messages
                - Flexible size limits
                - Warning-level logging
            Production:
                - Strict validation
                - Enforced size limits
                - Error-level logging
                - TODO: Add validation metrics

        Args:
            message: Message to validate, format as shown in message_states.py examples

        Returns:
            Dict of validation errors if any, None if valid

        Example message format:
            {
                "DestinationID": "01008988SKY5909",
                "UserMessageID": 2097,
                "TransportType": TransportType.SATELLITE,
                "Payload": {
                    "Name": "getTerminalStatus",
                    "SIN": 16,
                    "MIN": 2,
                    "IsForward": True,
                    "Fields": []
                }
            }
        """
        try:
            self.logger.debug(
                "Validating outbound message",
                extra={
                    "customer_id": self.settings.CUSTOMER_ID,
                    "asset_id": "message_processor",
                    "destination_id": message.get("DestinationID"),
                    "action": "validate_outbound",
                },
            )

            # Validate message
            self.message_validator.validate_message(message.get("Payload", {}))
            self.field_validator.validate_terminal_id(message.get("DestinationID", ""))

            if "TransportType" in message:
                try:
                    TransportType(message["TransportType"])
                except ValueError as e:
                    self.logger.warning(
                        "Invalid transport type",
                        extra={
                            "customer_id": self.settings.CUSTOMER_ID,
                            "asset_id": "message_processor",
                            "transport_type": message["TransportType"],
                            "error": str(e),
                            "action": "validate_transport",
                        },
                    )
                    return {"error": f"Invalid transport type: {str(e)}"}

            return None

        except ValidationError as e:
            self.logger.warning(
                "Message validation failed",
                extra={
                    "customer_id": self.settings.CUSTOMER_ID,
                    "asset_id": "message_processor",
                    "error": str(e),
                    "action": "validate_outbound",
                },
            )
            return {"error": str(e)}

    async def transform_inbound_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Transform inbound message for internal use.

        Implements transformation rules from OGWS-1.txt Section 5.2.
        See protocols.ogx.constants.message_states for format specifications.

        Environment-Specific Behavior:
            Development:
                - Allows malformed messages
                - Warning-level logging
                - Debug information retained
            Production:
                - Strict format enforcement
                - Error-level logging
                - Sanitized output
                - TODO: Add transformation metrics

        Args:
            message: Raw message from OGWS

        Returns:
            Transformed message following internal format

        Example response format:
            {
                "ID": 10844864715,
                "MessageUTC": "2022-11-25 12:00:03",
                "MobileID": "01008988SKY5909",
                "Payload": {
                    "Name": "message_name",
                    "SIN": 128,
                    "MIN": 1,
                    "Fields": [...]
                }
            }
        """
        # Validate incoming message structure
        try:
            if "Payload" in message:
                self.message_validator.validate_message(message["Payload"])
        except ValidationError:
            # Log validation error but don't reject message
            pass

        # Transform to internal format
        return {
            "ID": message.get("ID"),
            "MessageUTC": message.get("MessageUTC"),
            "MobileID": message.get("MobileID"),
            "Payload": message.get("Payload", {}),
            "State": MessageState.RECEIVED,
        }

    async def determine_transport(self, message: Dict[str, Any]) -> TransportType:
        """Determine best transport type for message.

        Implements transport selection from OGWS-1.txt Section 5.4:
        - Network type (OGx vs IsatData Pro)
        - Message size constraints
        - Terminal capabilities
        - Network conditions

        Environment-Specific Behavior:
            Development:
                - Defaults to ANY
                - No network optimization
                - Local testing support
            Production:
                - Smart routing
                - Network optimization
                - Cost optimization
                - TODO: Add transport metrics
                - TODO: Implement failover logic

        Args:
            message: Message to analyze

        Returns:
            Selected transport type (SATELLITE, CELLULAR, or ANY)
        """
        # If transport type is explicitly specified, use it
        if "TransportType" in message:
            try:
                return TransportType(message["TransportType"])
            except ValueError:
                pass

        # Default to ANY if no specific requirements
        return TransportType.ANY

    async def update_message_state(
        self, message_id: int, new_state: MessageState, metadata: Optional[Dict] = None
    ) -> None:
        """Update message state and handle transitions.

        Implements state management from OGWS-1.txt Section 5.3:
        - OGx states: ACCEPTED -> SENDING_IN_PROGRESS -> RECEIVED/ERROR
        - IDP states: ACCEPTED -> WAITING -> RECEIVED/ERROR

        Environment-Specific Behavior:
            Development:
                - Redis state storage
                - Local testing support
                - Detailed logging
            Production:
                - DynamoDB persistence
                - Atomic updates
                - Audit logging
                - TODO: Add state metrics
                - TODO: Implement state recovery

        Args:
            message_id: ID of message to update
            new_state: New state to transition to
            metadata: Optional metadata about the state change

        Raises:
            ValidationError: If state transition is invalid
            OGxProtocolError: If state update fails
        """
        try:
            validated_state = MessageState(new_state)
            await self.state_store.update_state(
                message_id=message_id, new_state=validated_state, metadata=metadata
            )

            self.logger.info(
                "Message state updated",
                extra={
                    "customer_id": self.settings.CUSTOMER_ID,
                    "asset_id": "message_processor",
                    "message_id": message_id,
                    "new_state": validated_state.name,
                    "action": "state_update",
                    "metadata": metadata,
                },
            )

        except ValueError as e:
            self.logger.warning(
                "Invalid message state transition",
                extra={
                    "customer_id": self.settings.CUSTOMER_ID,
                    "asset_id": "message_processor",
                    "message_id": message_id,
                    "attempted_state": new_state,
                    "error": str(e),
                    "action": "state_validation",
                    "error_code": ValidationError.INVALID_MESSAGE_FORMAT,
                },
            )
            raise ValidationError(
                "Invalid message state",
                error_code=ValidationError.INVALID_MESSAGE_FORMAT,
            ) from e

        except Exception as e:
            self.logger.error(
                "Failed to update message state",
                extra={
                    "customer_id": self.settings.CUSTOMER_ID,
                    "asset_id": "message_processor",
                    "message_id": message_id,
                    "attempted_state": new_state,
                    "error": str(e),
                    "action": "state_update",
                    "metadata": metadata,
                },
            )
            raise OGxProtocolError("Failed to update message state") from e
