"""Message processing metrics collection."""

from typing import Dict, Optional

from .backends.base import MetricsBackend


class MessageMetrics:
    """Collector for message processing metrics."""

    def __init__(self, backend: MetricsBackend):
        """Initialize message metrics collector.

        Args:
            backend: Metrics storage backend
        """
        self.backend = backend

    async def record_message_received(
        self,
        message_type: str,
        size: int,
        customer_id: Optional[str] = None,
        transport_type: Optional[str] = None,
    ) -> None:
        """Record a received message.

        Args:
            message_type: Type of message
            size: Size of message in bytes
            customer_id: Optional customer ID
            transport_type: Optional transport type
        """
        tags: Dict[str, str] = {"message_type": message_type}
        if customer_id:
            tags["customer_id"] = customer_id
        if transport_type:
            tags["transport_type"] = transport_type

        # Increment message counter
        await self.backend.increment("messages_received_total", 1, tags)

        # Record message size
        await self.backend.histogram("message_size_bytes", size, tags)

    async def record_message_processed(
        self,
        message_type: str,
        duration: float,
        success: bool,
        customer_id: Optional[str] = None,
        error_type: Optional[str] = None,
    ) -> None:
        """Record a processed message.

        Args:
            message_type: Type of message
            duration: Processing time in seconds
            success: Whether processing was successful
            customer_id: Optional customer ID
            error_type: Type of error if failed
        """
        tags: Dict[str, str] = {
            "message_type": message_type,
            "success": str(success),
        }
        if customer_id:
            tags["customer_id"] = customer_id
        if error_type and not success:
            tags["error_type"] = error_type

        # Increment processed counter
        await self.backend.increment("messages_processed_total", 1, tags)

        # Record processing time
        await self.backend.histogram("message_processing_duration_seconds", duration, tags)

    async def update_queue_metrics(
        self,
        queue_name: str,
        queue_size: int,
        in_progress: int,
        customer_id: Optional[str] = None,
    ) -> None:
        """Update queue-related metrics.

        Args:
            queue_name: Name of the queue
            queue_size: Current size of queue
            in_progress: Number of messages being processed
            customer_id: Optional customer ID
        """
        tags: Dict[str, str] = {"queue": queue_name}
        if customer_id:
            tags["customer_id"] = customer_id

        # Update queue metrics
        await self.backend.gauge("message_queue_size", queue_size, tags)
        await self.backend.gauge("messages_in_progress", in_progress, tags)
