"""Network condition monitoring for transport optimization.

This module provides interfaces and implementations for monitoring network conditions
to support intelligent transport selection. It tracks:
- Network availability
- Signal strength
- Latency
- Error rates
- Cost metrics

Implementation follows OGx-1.txt specifications:
- Section 5.4: Transport Selection
- Section 4.2: Rate Limiting and Quotas
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Optional

from Protexis_Command.api.config import TransportType
from Protexis_Command.core.logging.loggers import get_protocol_logger


class NetworkMetrics:
    """Container for network condition metrics."""

    def __init__(
        self,
        transport_type: TransportType,
        signal_strength: Optional[float] = None,
        latency_ms: Optional[float] = None,
        error_rate: Optional[float] = None,
        availability: Optional[float] = None,
        last_successful_message: Optional[datetime] = None,
    ):
        """Initialize network metrics.

        Args:
            transport_type: Type of transport these metrics are for
            signal_strength: Signal strength in dB (if applicable)
            latency_ms: Average latency in milliseconds
            error_rate: Error rate as percentage (0-100)
            availability: Network availability percentage (0-100)
            last_successful_message: Timestamp of last successful message
        """
        self.transport_type = transport_type
        self.signal_strength = signal_strength
        self.latency_ms = latency_ms
        self.error_rate = error_rate
        self.availability = availability
        self.last_successful_message = last_successful_message
        self.timestamp = datetime.utcnow()


class NetworkMonitor(ABC):
    """Abstract base class for network condition monitoring."""

    @abstractmethod
    async def get_network_metrics(self, transport_type: TransportType) -> NetworkMetrics:
        """Get current metrics for specified transport type.

        Args:
            transport_type: Transport type to get metrics for

        Returns:
            Current network metrics
        """
        raise NotImplementedError  # Replace pass with raise NotImplementedError

    @abstractmethod
    async def update_metrics(
        self,
        transport_type: TransportType,
        success: bool,
        latency_ms: Optional[float] = None,
        error_info: Optional[Dict] = None,
    ) -> None:
        """Update metrics based on message send attempt.

        Args:
            transport_type: Transport type used
            success: Whether message send was successful
            latency_ms: Message round-trip time if available
            error_info: Error details if send failed
        """
        raise NotImplementedError  # Replace pass with raise NotImplementedError


class DefaultNetworkMonitor(NetworkMonitor):
    """Default implementation of network condition monitoring."""

    def __init__(self) -> None:
        """Initialize network monitor."""
        self._metrics: Dict[TransportType, NetworkMetrics] = {}
        self._error_counts: Dict[TransportType, int] = {}
        self._success_counts: Dict[TransportType, int] = {}
        self.logger = get_protocol_logger("network_monitor")

    async def get_network_metrics(self, transport_type: TransportType) -> NetworkMetrics:
        """Get current metrics for specified transport type.

        If no metrics exist, returns new metrics with default values.

        Args:
            transport_type: Transport type to get metrics for

        Returns:
            Current network metrics
        """
        if transport_type not in self._metrics:
            self._metrics[transport_type] = NetworkMetrics(transport_type)
        return self._metrics[transport_type]

    async def update_metrics(
        self,
        transport_type: TransportType,
        success: bool,
        latency_ms: Optional[float] = None,
        error_info: Optional[Dict] = None,
    ) -> None:
        """Update metrics based on message send attempt.

        Updates:
        - Success/error counts
        - Average latency
        - Error rate
        - Last successful message timestamp

        Args:
            transport_type: Transport type used
            success: Whether message send was successful
            latency_ms: Message round-trip time if available
            error_info: Error details if send failed
        """
        if transport_type not in self._metrics:
            self._metrics[transport_type] = NetworkMetrics(transport_type)

        metrics = self._metrics[transport_type]

        # Update counts
        if success:
            self._success_counts[transport_type] = self._success_counts.get(transport_type, 0) + 1
            metrics.last_successful_message = datetime.utcnow()
        else:
            self._error_counts[transport_type] = self._error_counts.get(transport_type, 0) + 1

        # Update error rate
        total_attempts = self._success_counts.get(transport_type, 0) + self._error_counts.get(
            transport_type, 0
        )
        if total_attempts > 0:
            metrics.error_rate = (self._error_counts.get(transport_type, 0) / total_attempts) * 100

        # Update latency if provided
        if latency_ms is not None:
            if metrics.latency_ms is None:
                metrics.latency_ms = latency_ms
            else:
                # Exponential moving average
                alpha = 0.2  # Smoothing factor
                metrics.latency_ms = (alpha * latency_ms) + ((1 - alpha) * metrics.latency_ms)

        # Log metrics update
        self.logger.debug(
            "Network metrics updated",
            extra={
                "transport_type": transport_type.name,
                "success": success,
                "latency_ms": latency_ms,
                "error_rate": metrics.error_rate,
                "error_info": error_info,
            },
        )
