"""Base interface for metrics backends."""

from abc import ABC, abstractmethod
from typing import Dict, Optional, Union

# Type aliases
MetricValue = Union[int, float]
MetricTags = Dict[str, str]


class MetricsBackend(ABC):
    """Abstract base class for metrics backends."""

    @abstractmethod
    async def increment(
        self,
        name: str,
        value: MetricValue = 1,
        tags: Optional[MetricTags] = None,
    ) -> None:
        """Increment a counter metric.

        Args:
            name: Name of the metric
            value: Value to increment by (default: 1)
            tags: Optional tags/labels for the metric
        """

    @abstractmethod
    async def gauge(
        self,
        name: str,
        value: MetricValue,
        tags: Optional[MetricTags] = None,
    ) -> None:
        """Set a gauge metric.

        Args:
            name: Name of the metric
            value: Value to set
            tags: Optional tags/labels for the metric
        """

    @abstractmethod
    async def histogram(
        self,
        name: str,
        value: MetricValue,
        tags: Optional[MetricTags] = None,
    ) -> None:
        """Record a histogram observation.

        Args:
            name: Name of the metric
            value: Value to observe
            tags: Optional tags/labels for the metric
        """

    @abstractmethod
    async def summary(
        self,
        name: str,
        value: MetricValue,
        tags: Optional[MetricTags] = None,
    ) -> None:
        """Record a summary observation.

        Args:
            name: Name of the metric
            value: Value to observe
            tags: Optional tags/labels for the metric
        """
