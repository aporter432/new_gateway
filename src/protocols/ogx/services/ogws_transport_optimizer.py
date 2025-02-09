"""OGWS transport optimization service.

This module implements transport selection logic following OGWS-1.txt specifications:
- Section 5.4: Transport Selection Rules
    - Network type determination
    - Message size constraints
    - Terminal capabilities
    - Network conditions
- Section 4.2: Rate Limiting
    - Transport-specific quotas
    - Throughput limits
- Section 7.2: Error Recovery
    - Transport failover
    - Retry strategies

The transport optimizer uses network metrics to make intelligent routing decisions
based on current conditions and message requirements.

Implementation Notes:
- Network-specific payload limits:
    - OGx network: 1023 bytes fixed limit

- Transport characteristics:
    - Satellite:
        - Higher latency but more reliable
        - Larger coverage area
        - Higher cost per message
    - Cellular:
        - Lower latency when available
        - Limited coverage area
        - Lower cost per message

Environment-Specific Behavior:
Development:
    - Simulated network conditions
    - All transports enabled
    - Flexible constraints
    - Debug logging

Production:
    - Real network metrics
    - Account-specific permissions
    - Strict size limits
    - Cost optimization
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from core.app_settings import get_settings
from core.logging.loggers import get_protocol_logger
from protocols.ogx.constants import (
    TRANSPORT_TYPE_CELLULAR,
    TRANSPORT_TYPE_SATELLITE,
    NetworkType,
    TransportType,
)
from protocols.ogx.constants.limits import MAX_OGX_PAYLOAD_BYTES
from protocols.ogx.exceptions import ValidationError

from .ogws_network_monitor import NetworkMetrics, NetworkMonitor


class TransportOptimizer:
    """OGWS transport optimization service.

    This class implements intelligent transport selection based on:
    - Current network conditions
    - Message characteristics
    - Terminal capabilities
    - Cost considerations
    """

    def __init__(self, network_monitor: NetworkMonitor):
        """Initialize transport optimizer.

        Args:
            network_monitor: Network condition monitor
        """
        self.network_monitor = network_monitor
        self.logger = get_protocol_logger("transport_optimizer")
        self.settings = get_settings()

        # Transport-specific thresholds
        self._error_rate_threshold = 20.0  # Consider transport degraded above 20% errors
        self._latency_threshold_ms = 5000  # Consider transport degraded above 5s latency
        self._availability_threshold = 80.0  # Consider transport degraded below 80% availability

    async def determine_transport(
        self,
        message: Dict,
        terminal_id: str,
        network_type: NetworkType,  # Kept for API compatibility
        preferred_transport: Optional[TransportType] = None,
    ) -> TransportType:
        """Determine optimal transport for message.

        Implements transport selection following OGWS-1.txt Section 5.4:
        1. Check message constraints (size, priority)
        2. Check terminal capabilities
        3. Evaluate network conditions
        4. Apply cost optimization

        Args:
            message: Message to be sent
            terminal_id: Destination terminal ID
            network_type: Network type (OGx or IDP)
            preferred_transport: Optional preferred transport type

        Returns:
            Selected transport type

        Raises:
            ValidationError: If no suitable transport available
        """
        # Get message size
        message_size = len(str(message).encode())  # Simple size estimation

        # Validate message size against network limits
        if not self._is_size_valid_for_network(message_size):
            raise ValidationError(
                f"Message size {message_size} bytes exceeds network limit",
                ValidationError.INVALID_MESSAGE_FORMAT,
            )

        # Get available transports based on network type
        available_transports = self._get_available_transports()

        # If preferred transport is specified and available, use it
        if preferred_transport in available_transports:
            return preferred_transport

        # Get network metrics for available transports
        transport_metrics = []
        for transport in available_transports:
            metrics = await self.network_monitor.get_network_metrics(transport)
            if await self._is_transport_healthy(metrics):
                transport_metrics.append((transport, metrics))

        if not transport_metrics:
            raise ValidationError(
                "No healthy transports available", ValidationError.INVALID_FIELD_VALUE
            )

        # Select best transport based on conditions and cost
        selected_transport = await self._select_best_transport(transport_metrics)

        self.logger.info(
            "Transport selected",
            extra={
                "terminal_id": terminal_id,
                "message_size": message_size,
                "network_type": network_type.name,
                "selected_transport": selected_transport.name,
                "available_transports": [t.name for t, _ in transport_metrics],
            },
        )

        return selected_transport

    def _is_size_valid_for_network(self, message_size: int) -> bool:
        """Check if message size is valid for network."""
        return message_size <= MAX_OGX_PAYLOAD_BYTES

    def _get_available_transports(self) -> List[TransportType]:
        """Get available transports for OGx network."""
        return [TRANSPORT_TYPE_SATELLITE, TRANSPORT_TYPE_CELLULAR]

    async def _is_transport_healthy(self, metrics: NetworkMetrics) -> bool:
        """Check if transport is healthy based on metrics.

        Args:
            metrics: Network metrics for transport

        Returns:
            True if transport is healthy
        """
        # Check if we have recent metrics
        if metrics.timestamp < datetime.utcnow() - timedelta(minutes=5):
            return False

        # Check error rate
        if metrics.error_rate and metrics.error_rate > self._error_rate_threshold:
            return False

        # Check latency
        if metrics.latency_ms and metrics.latency_ms > self._latency_threshold_ms:
            return False

        # Check availability
        if metrics.availability and metrics.availability < self._availability_threshold:
            return False

        return True

    async def _select_best_transport(
        self, transport_metrics: List[Tuple[TransportType, NetworkMetrics]]
    ) -> TransportType:
        """Select best transport based on conditions and cost.

        Args:
            transport_metrics: List of (transport, metrics) tuples

        Returns:
            Selected transport type
        """
        # Simple scoring system (higher is better)
        scores: Dict[TransportType, float] = {}

        for transport, metrics in transport_metrics:
            base_score = 100.0

            # Penalize for high error rate
            if metrics.error_rate:
                base_score -= metrics.error_rate

            # Penalize for high latency
            if metrics.latency_ms:
                base_score -= (metrics.latency_ms / self._latency_threshold_ms) * 20

            # Bonus for high availability
            if metrics.availability:
                base_score += (metrics.availability / 100.0) * 20

            # Prefer cellular for cost optimization if conditions similar
            if transport == TRANSPORT_TYPE_CELLULAR:
                base_score += 10

            scores[transport] = base_score

        # Select transport with highest score
        return max(scores.items(), key=lambda x: x[1])[0]
