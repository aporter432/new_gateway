"""Operation modes for OGWS terminals.

This module defines the operation modes that control terminal behavior and power management
as specified in OGWS-1.txt.

Operation modes determine:
- How terminals handle message reception and transmission
- Power consumption and wake/sleep cycles
- Network-specific capabilities and restrictions
- Message delivery timing and batching

Usage Examples:

    from protocols.ogx.constants import OperationMode, NetworkType

    def select_power_mode(
        battery_level: float,
        is_time_critical: bool,
        network: NetworkType
    ) -> OperationMode:
        '''Select appropriate operation mode based on conditions.'''
        if battery_level < 0.2:  # Critical battery
            return OperationMode.WAKE_UP  # Lowest power consumption
        
        if is_time_critical:
            return OperationMode.ALWAYS_ON  # Best responsiveness
            
        if network == NetworkType.OGX:
            return OperationMode.HYBRID  # Balanced for OGx
            
        return OperationMode.WAKE_UP  # Default to power saving

    def estimate_daily_power_mah(mode: OperationMode) -> float:
        '''Estimate daily power consumption in mAh.'''
        consumption = {
            OperationMode.ALWAYS_ON: 240.0,        # 10mA continuous
            OperationMode.WAKE_UP: 24.0,           # 1mA average
            OperationMode.MOBILE_RECEIVE_ON_SEND: 120.0,  # 5mA average
            OperationMode.HYBRID: 180.0            # 7.5mA average
        }
        return consumption.get(mode, 240.0)

    def is_mode_supported(mode: OperationMode, network: NetworkType) -> bool:
        '''Check if operation mode is supported on network.'''
        if network == NetworkType.ISAT_DATA_PRO:
            # IDP only supports ALWAYS_ON and WAKE_UP
            return mode in (OperationMode.ALWAYS_ON, OperationMode.WAKE_UP)
        # OGx supports all modes
        return True

Implementation Notes:
    - ALWAYS_ON provides lowest latency but highest power use
    - WAKE_UP uses least power but has highest latency
    - MOBILE_RECEIVE_ON_SEND and HYBRID only available on OGx network
    - Mode changes require terminal reboot
    - Wake-up intervals are configurable per terminal
    - Power consumption varies by network type
    - Consider power budget when selecting mode
    - Some features only available in specific modes
    - Network type affects available modes
"""

from enum import IntEnum


class OperationMode(IntEnum):
    """Operation modes as defined in OGWS-1.txt.

    Controls how terminals handle messages and power management:
    - ALWAYS_ON: Continuous connection (highest power, lowest latency)
    - WAKE_UP: Periodic wake-up (lowest power, highest latency)
    - MOBILE_RECEIVE_ON_SEND: Only receives when sending (medium power/latency)
    - HYBRID: Mixed mode operation (balanced power/latency)

    Network Support:
    - ALWAYS_ON: Supported on both OGx and IsatData Pro
    - WAKE_UP: Supported on both OGx and IsatData Pro
    - MOBILE_RECEIVE_ON_SEND: OGx only
    - HYBRID: OGx only

    Power Consumption (relative):
    - ALWAYS_ON: Highest (~10mA continuous)
    - WAKE_UP: Lowest (~1mA average)
    - MOBILE_RECEIVE_ON_SEND: Medium (~5mA average)
    - HYBRID: Medium-High (~7.5mA average)

    Usage:
        def configure_terminal(
            terminal_id: str,
            battery_level: float,
            network: NetworkType
        ) -> None:
            '''Configure terminal operation mode based on conditions.'''
            if battery_level < 0.2:  # Critical battery
                if network == NetworkType.OGX:
                    set_mode(terminal_id, OperationMode.MOBILE_RECEIVE_ON_SEND)
                else:
                    set_mode(terminal_id, OperationMode.WAKE_UP)
            else:
                set_mode(terminal_id, OperationMode.ALWAYS_ON)

        def get_mode_description(mode: OperationMode) -> str:
            '''Get human-readable mode description.'''
            descriptions = {
                OperationMode.ALWAYS_ON: "Continuous connection, immediate delivery",
                OperationMode.WAKE_UP: "Periodic wake-up, delayed delivery",
                OperationMode.MOBILE_RECEIVE_ON_SEND: "Receive only when sending",
                OperationMode.HYBRID: "Dynamic power/delivery balance"
            }
            return descriptions.get(mode, "Unknown mode")

    Implementation Notes:
        - Mode changes require terminal reboot
        - Consider network capabilities when setting mode
        - Monitor power consumption in each mode
        - Test message delivery timing in each mode
        - Implement appropriate retry logic
        - Handle mode change failures gracefully
        - Log mode changes for diagnostics
        - Consider environmental conditions
    """

    ALWAYS_ON = 0  # Continuous connection (IDP/OGx)
    WAKE_UP = 1  # Periodic wake-up (IDP/OGx)
    MOBILE_RECEIVE_ON_SEND = 2  # Receive on send (OGx only)
    HYBRID = 3  # Mixed mode (OGx only)
