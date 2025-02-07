"""Operation modes and network types as defined in OGWS-1.txt.

This module defines:
- Network types supported by terminals (IDP/OGx)
- Operation modes that control terminal behavior and power management

These constants determine:
- How terminals handle message reception and transmission
- Power consumption and wake/sleep cycles
- Message size limits and delivery options
- Network-specific capabilities and restrictions

Usage:
    from protocols.ogx.constants import NetworkType, OperationMode

    # Validate message size for network
    def validate_payload_size(network: NetworkType, payload: bytes) -> bool:
        max_size = {
            NetworkType.IDP: 10000,  # IDP supports larger payloads
            NetworkType.OGX: 1023,   # OGx has smaller payload limit
        }
        return len(payload) <= max_size.get(network, 0)

    # Configure terminal power mode
    def configure_terminal(terminal_id: str, battery_level: float) -> None:
        if battery_level < 0.2:  # Critical battery
            set_mode(terminal_id, OperationMode.WAKE_UP)  # Lowest power
        elif battery_level < 0.5:  # Low battery
            set_mode(terminal_id, OperationMode.SEND_ON_RECEIVE)  # Medium power
        else:
            set_mode(terminal_id, OperationMode.ALWAYS_ON)  # Best responsiveness

Implementation Notes:
    - Network type affects message size limits and features
    - Operation mode impacts power consumption and latency
    - Mode changes require terminal reboot
    - Some modes only available on specific networks
    - Consider power budget when selecting mode
    - Network determines available features

Network Types:
    IDP Network:
    - High latency, high reliability
    - Global coverage
    - Large message support
    - Higher cost per message

    OGx Network:
    - Low latency, variable reliability
    - Regional coverage
    - Small message optimization
    - Lower cost per message

Operation Modes:
    1. ALWAYS_ON:
       - Continuous network connection
       - Immediate message delivery
       - Higher power consumption
       - Best for time-critical data

    2. POWER_SAVE:
       - Periodic network checks
       - Delayed message delivery
       - Optimized power usage
       - Best for battery life

    3. HYBRID:
       - Dynamic power management
       - Priority-based activation
       - Balanced power/delivery
       - Best for mixed workloads

Cross-Network Message Routing Rules:

    1. Network Selection Criteria:
       Primary Factors:
       - Message size and priority
       - Network availability
       - Terminal capabilities
       - Cost considerations

       Secondary Factors:
       - Historical performance
       - Current network load
       - Time of day patterns
       - Geographic location

    2. Routing Decision Matrix:
       High Priority Messages:
       - Size <= 400B: OGx preferred
       - Size > 400B: IDP preferred
       - Fallback: Any available network

       Normal Priority Messages:
       - Size <= 1KB: Network availability
       - Size > 1KB: IDP only
       - Fallback: Queue for retry

       Low Priority Messages:
       - Size <= 2KB: Cost optimization
       - Size > 2KB: IDP off-peak
       - Fallback: Store and forward

    3. Terminal State Impact:
       Active Mode:
       - Use optimal network
       - Immediate delivery attempt
       - Dynamic network switching

       Power Save Mode:
       - Queue until wake window
       - Batch similar messages
       - Prefer scheduled delivery

       Hybrid Mode:
       - Priority determines timing
       - Network cost optimization
       - Adaptive scheduling

    4. Error Handling Strategy:
       Network Unavailable:
       - Queue for retry
       - Try alternate network
       - Notify if urgent

       Delivery Failure:
       - Retry on same network
       - Switch networks if persistent
       - Escalate if critical

       Resource Constraints:
       - Throttle submissions
       - Prioritize queue
       - Drop lowest priority

Usage:
    from protocols.ogx.constants import NetworkType, OperationMode

    def select_network(message: dict, terminal: dict) -> NetworkType:
        # Get message characteristics
        size = len(message["payload"])
        priority = message.get("priority", "normal")
        
        # Get terminal state
        mode = terminal.get("operation_mode", OperationMode.ALWAYS_ON)
        location = terminal.get("location")
        battery = terminal.get("battery_level", 100)

        # Apply routing rules
        if priority == "high":
            if size <= 400:
                return NetworkType.OGX
            return NetworkType.IDP

        if mode == OperationMode.POWER_SAVE:
            if battery < 20:
                return NetworkType.IDP  # More efficient
            return NetworkType.ANY  # Let gateway optimize

        if size > 1024:
            return NetworkType.IDP

        # Default to cost-effective option
        return NetworkType.OGX

    def handle_delivery_failure(message: dict, attempt: int) -> dict:
        if attempt < 3:
            return {"action": "retry", "delay": 300}  # 5 min
        
        if message["priority"] == "high":
            return {"action": "alternate_network"}
            
        return {"action": "queue", "delay": 3600}  # 1 hour

Implementation Notes:
    Network Selection:
    - Consider message characteristics
    - Check terminal capabilities
    - Evaluate network conditions
    - Apply cost optimization

    Operation Modes:
    - Mode changes affect routing
    - Power state impacts timing
    - Priority overrides defaults
    - Batch processing allowed

    Error Recovery:
    - Progressive retry delays
    - Network switching logic
    - Priority escalation
    - Queue management

    Performance Optimization:
    - Cache routing decisions
    - Batch similar messages
    - Predict network availability
    - Learn from history

    Monitoring Requirements:
    - Track delivery success
    - Measure network performance
    - Log routing decisions
    - Report anomalies
"""

from enum import Enum


class NetworkType(int, Enum):
    """Network types as defined in OGWS-1.txt.

    Specifies the satellite network type:
    - IDP: IsatData Pro network (up to 10000 bytes payload)
    - OGX: OG2 network (up to 1023 bytes payload)

    Usage:
        # Format message based on network
        def format_message(data: dict, network: NetworkType) -> dict:
            if network == NetworkType.IDP:
                return format_idp_message(data, max_size=10000)
            elif network == NetworkType.OGX:
                return format_ogx_message(data, max_size=1023)
            raise ValueError(f"Unsupported network: {network}")

        # Check network capabilities
        def supports_large_messages(network: NetworkType) -> bool:
            return network == NetworkType.IDP

        # Get network-specific timeout
        def get_message_timeout(network: NetworkType) -> int:
            timeouts = {
                NetworkType.IDP: 86400,  # 24 hours for IDP
                NetworkType.OGX: 43200   # 12 hours for OGx
            }
            return timeouts.get(network, 43200)

    Implementation Notes:
        - IDP optimized for larger messages (up to 10000 bytes)
        - OGX optimized for efficient delivery (up to 1023 bytes)
        - Network determines available features
        - Message size limits strictly enforced
        - Each network has specific timing characteristics
        - Network affects power consumption
        - Consider network capabilities when designing messages
        - Some features only available on specific networks
    """

    IDP = 0  # IsatData Pro network
    OGX = 1  # OG2 network


class OperationMode(int, Enum):
    """Operation modes as defined in OGWS-1.txt.

    Controls how terminals handle messages:
    - ALWAYS_ON: Continuous connection (highest power, lowest latency)
    - WAKE_UP: Periodic wake-up (lowest power, highest latency)
    - SEND_ON_RECEIVE: Only receives when sending (medium power/latency)
    - HYBRID: Mixed mode operation (balanced power/latency)

    Usage:
        # Select mode based on requirements
        def select_operation_mode(
            battery_powered: bool,
            latency_sensitive: bool,
            network: NetworkType
        ) -> OperationMode:
            if not battery_powered:
                return OperationMode.ALWAYS_ON
            if latency_sensitive:
                return OperationMode.HYBRID if network == NetworkType.OGX else OperationMode.ALWAYS_ON
            return OperationMode.WAKE_UP

        # Calculate power consumption
        def estimate_daily_power_mah(mode: OperationMode) -> float:
            consumption = {
                OperationMode.ALWAYS_ON: 240.0,        # 10mA continuous
                OperationMode.WAKE_UP: 24.0,          # 1mA average
                OperationMode.SEND_ON_RECEIVE: 120.0, # 5mA average
                OperationMode.HYBRID: 180.0           # 7.5mA average
            }
            return consumption.get(mode, 240.0)

        # Check mode compatibility
        def is_mode_supported(mode: OperationMode, network: NetworkType) -> bool:
            if network == NetworkType.IDP:
                return mode in (OperationMode.ALWAYS_ON, OperationMode.WAKE_UP)
            return True  # All modes supported on OGx

    Implementation Notes:
        - Mode affects power consumption significantly
        - WAKE_UP uses least power but has highest latency
        - ALWAYS_ON provides lowest latency but highest power use
        - Some modes restricted by network type
        - Consider power budget when selecting mode
        - Mode changes require terminal reboot
        - SEND_ON_RECEIVE and HYBRID only available on OGx
        - Wake-up intervals configurable per terminal
        - Power consumption varies by network type
        - Latency varies by mode and network
    """

    ALWAYS_ON = 0  # Continuous connection (IDP/OGx)
    WAKE_UP = 1  # Periodic wake-up (IDP/OGx)
    SEND_ON_RECEIVE = 2  # Receive on send (OGx only)
    HYBRID = 3  # Mixed mode (OGx only)
