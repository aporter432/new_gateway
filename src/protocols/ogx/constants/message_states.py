"""Transport types and message states as defined in OGWS-1.txt.

This module defines:
- Message states that track the lifecycle of messages in the system
- Transport types that specify how messages should be delivered
- Network-specific timeout behaviors and error handling
- Cross-network message routing rules

These constants are used to:
- Monitor message delivery status and handle errors
- Control message routing through available transport channels
- Manage message lifecycle from submission to completion
- Handle network-specific timeouts and retries

Network Timeout Handling:
    OGx Network:
    - Initial timeout: 5 minutes
    - Retry interval: 10 minutes
    - Max retries: 3
    - Final timeout: 12 hours

    IDP Network:
    - Initial timeout: 15 minutes
    - Retry interval: 30 minutes
    - Max retries: 5
    - Final timeout: 24 hours

Error State Handling:
    Transient Errors (Retryable):
    - Network congestion
    - Temporary terminal unavailable
    - Gateway processing delays
    - Beam handover in progress

    Terminal Errors (Non-Retryable):
    - Invalid terminal ID
    - Terminal deactivated
    - Message size exceeds limit
    - Invalid message format

    System Errors (Requires Investigation):
    - Gateway internal error
    - Database connectivity issues
    - Network subsystem failure
    - Configuration errors

Cross-Network Routing:
    Message Size Based:
    - Small messages (<400 bytes): Either network
    - Medium messages (400-1023 bytes): Either network
    - Large messages (1024-10000 bytes): IDP only

    Priority Based:
    - High priority: Prefer OGx for faster delivery
    - Normal priority: Network availability based
    - Low priority: Cost optimization based

    Terminal State Based:
    - Active terminals: Primary network
    - Power-saving mode: Wait for wake-up
    - Hybrid mode: Network availability based

Usage:
    from protocols.ogx.constants import MessageState, TransportType

    # Handle network-specific timeouts
    def get_timeout_config(network: str, message_size: int) -> dict:
        if network == "OGX":
            return {
                "initial_timeout": timedelta(minutes=5),
                "retry_interval": timedelta(minutes=10),
                "max_retries": 3,
                "final_timeout": timedelta(hours=12)
            }
        else:  # IDP
            return {
                "initial_timeout": timedelta(minutes=15),
                "retry_interval": timedelta(minutes=30),
                "max_retries": 5,
                "final_timeout": timedelta(hours=24)
            }

    # Determine if error is retryable
    def is_retryable_error(state: MessageState, error_code: int) -> bool:
        transient_errors = {
            "network_congestion": range(1000, 1100),
            "temp_unavailable": range(2000, 2100),
            "gateway_delay": range(3000, 3100),
            "beam_handover": range(4000, 4100)
        }
        return any(error_code in codes for codes in transient_errors.values())

    # Select optimal transport
    def select_transport(message: dict, terminal: dict) -> TransportType:
        size = len(message["payload"])
        if size > 1023:
            return TransportType.SATELLITE  # Force IDP for large messages
        
        if message.get("priority") == "high":
            return TransportType.SATELLITE  # OGx for speed
        
        if terminal["power_mode"] == "sleep":
            return TransportType.ANY  # Wait for wake-up
        
        return TransportType.CELLULAR  # Default to cost-effective

Implementation Notes:
    - Message state transitions are one-way and final for completion states
    - Transport selection affects delivery timing and costs
    - Default transport (ANY) lets gateway optimize delivery
    - Some states are network-specific (e.g. DELAYED_SEND for IDP only)
    - Timeout handling varies by network and message size
    - Error recovery strategy depends on error type
    - Cross-network routing considers multiple factors
    - Network selection impacts delivery guarantees
"""

from enum import Enum


class MessageState(int, Enum):
    """Message states as defined in OGWS-1.txt.

    Tracks the lifecycle of messages through the system:
    - ACCEPTED: Initial state after Gateway accepts message
    - RECEIVED: Successfully delivered to destination
    - ERROR: Failed with submission error (check error code)
    - DELIVERY_FAILED: Failed to deliver (check error code)
    - TIMED_OUT: Exceeded delivery timeout (10 days)
    - CANCELLED: Manually cancelled by user
    - DELAYED_SEND: Queued for delayed delivery (IDP only)
    - BROADCAST_SUBMITTED: Broadcast message sent
    - SENDING_IN_PROGRESS: Currently being transmitted (OGx only)

    Usage:
        # Handle message completion
        def on_message_state_change(message_id: int, state: MessageState) -> None:
            if state == MessageState.RECEIVED:
                mark_delivered(message_id)
            elif state in (MessageState.ERROR, MessageState.DELIVERY_FAILED):
                handle_failure(message_id)
            elif state == MessageState.TIMED_OUT:
                notify_timeout(message_id)

        # Check if message needs retry
        def should_retry_message(state: MessageState) -> bool:
            return state in (
                MessageState.ERROR,
                MessageState.DELIVERY_FAILED,
                MessageState.TIMED_OUT
            )

        # Get user-friendly status
        def get_status_description(state: MessageState) -> str:
            status_map = {
                MessageState.ACCEPTED: "Message accepted by gateway",
                MessageState.RECEIVED: "Successfully delivered",
                MessageState.ERROR: "Submission error occurred",
                MessageState.DELIVERY_FAILED: "Delivery attempt failed",
                MessageState.TIMED_OUT: "Message timed out",
                MessageState.CANCELLED: "Cancelled by user",
                MessageState.DELAYED_SEND: "Queued for delayed delivery",
                MessageState.BROADCAST_SUBMITTED: "Broadcast submitted",
                MessageState.SENDING_IN_PROGRESS: "Transmission in progress"
            }
            return status_map.get(state, "Unknown state")

    Implementation Notes:
        - States are terminal once reaching a completion state
        - Error states include additional error codes
        - Timeout period is 10 days for offline terminals
        - State changes trigger notifications to client
        - Some states are specific to IDP or OGx networks
        - State transitions are one-way and cannot be reversed
        - Check error codes when in ERROR or DELIVERY_FAILED states
        - DELAYED_SEND is only valid for IDP network messages
        - SENDING_IN_PROGRESS is only valid for OGx network messages
    """

    ACCEPTED = 0
    RECEIVED = 1
    ERROR = 2
    DELIVERY_FAILED = 3
    TIMED_OUT = 4
    CANCELLED = 5
    DELAYED_SEND = 6  # IDP network only
    BROADCAST_SUBMITTED = 7
    SENDING_IN_PROGRESS = 8  # OGx network only


class TransportType(int, Enum):
    """Transport types as defined in OGWS-1.txt.

    Specifies the communication channel for message delivery:
    - ANY: Use any available transport (default)
    - SATELLITE: Restrict to satellite network only
    - CELLULAR: Restrict to cellular network only

    Usage:
        # Select transport based on message priority
        def submit_message(message: dict, priority: str) -> None:
            transport = TransportType.ANY
            if priority == "high":
                transport = TransportType.SATELLITE  # Most reliable
            elif priority == "low":
                transport = TransportType.CELLULAR  # Cost-effective

            submit_to_gateway(message, transport=transport)

        # Check if message can use cellular
        def can_use_cellular(message: dict) -> bool:
            return (
                message.get("transport") in (TransportType.ANY, TransportType.CELLULAR)
                and is_cellular_available()
            )

        # Get transport cost factor
        def get_cost_factor(transport: TransportType) -> float:
            cost_map = {
                TransportType.ANY: 1.0,  # Base cost
                TransportType.SATELLITE: 1.5,  # 50% premium
                TransportType.CELLULAR: 0.7,  # 30% discount
            }
            return cost_map.get(transport, 1.0)

    Implementation Notes:
        - ANY allows gateway to optimize delivery path
        - SATELLITE provides most reliable delivery
        - CELLULAR offers cost-effective delivery
        - Transport affects timing and delivery guarantees
        - Some features only available on specific transports
        - Gateway may override ANY based on conditions
        - SATELLITE has highest priority but costs more
        - CELLULAR may not be available in all regions
        - Transport selection impacts message timing
    """

    ANY = 0  # Default - any transport
    SATELLITE = 1
    CELLULAR = 2
