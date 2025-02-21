"""Prometheus metrics backend implementation."""

from typing import Dict, Optional, Union

import prometheus_client as prom
from prometheus_client.metrics import Counter, Gauge, Histogram, Summary

from .base import MetricsBackend

# Type alias for metric values
MetricValue = Union[int, float]

# Default buckets for histograms (in seconds)
DEFAULT_DURATION_BUCKETS = (
    0.005,
    0.01,
    0.025,
    0.05,
    0.075,
    0.1,
    0.25,
    0.5,
    0.75,
    1.0,
    2.5,
    5.0,
    7.5,
    10.0,
)


class PrometheusBackend(MetricsBackend):
    """Prometheus implementation of metrics backend."""

    def __init__(self) -> None:
        """Initialize the Prometheus backend."""
        self._counters: Dict[str, Counter] = {}
        self._gauges: Dict[str, Gauge] = {}
        self._histograms: Dict[str, Histogram] = {}
        self._summaries: Dict[str, Summary] = {}

    def _get_counter(self, name: str, tags: Optional[Dict[str, str]] = None) -> Counter:
        """Get or create a Counter metric.

        Args:
            name: Name of the metric
            tags: Optional tags/labels for the metric

        Returns:
            The Counter metric
        """
        if name not in self._counters:
            self._counters[name] = Counter(
                name,
                name.replace("_", " ").capitalize(),
                list(tags.keys()) if tags else [],
            )
        return self._counters[name]

    def _get_gauge(self, name: str, tags: Optional[Dict[str, str]] = None) -> Gauge:
        """Get or create a Gauge metric.

        Args:
            name: Name of the metric
            tags: Optional tags/labels for the metric

        Returns:
            The Gauge metric
        """
        if name not in self._gauges:
            self._gauges[name] = Gauge(
                name,
                name.replace("_", " ").capitalize(),
                list(tags.keys()) if tags else [],
            )
        return self._gauges[name]

    def _get_histogram(
        self,
        name: str,
        tags: Optional[Dict[str, str]] = None,
        buckets: tuple[float, ...] = DEFAULT_DURATION_BUCKETS,
    ) -> Histogram:
        """Get or create a Histogram metric.

        Args:
            name: Name of the metric
            tags: Optional tags/labels for the metric
            buckets: Histogram buckets

        Returns:
            The Histogram metric
        """
        if name not in self._histograms:
            self._histograms[name] = Histogram(
                name,
                name.replace("_", " ").capitalize(),
                list(tags.keys()) if tags else [],
                buckets=buckets,
            )
        return self._histograms[name]

    def _get_summary(
        self,
        name: str,
        tags: Optional[Dict[str, str]] = None,
    ) -> Summary:
        """Get or create a Summary metric.

        Args:
            name: Name of the metric
            tags: Optional tags/labels for the metric

        Returns:
            The Summary metric
        """
        if name not in self._summaries:
            self._summaries[name] = Summary(
                name,
                name.replace("_", " ").capitalize(),
                list(tags.keys()) if tags else [],
            )
        return self._summaries[name]

    async def increment(
        self,
        name: str,
        value: MetricValue = 1,
        tags: Optional[Dict[str, str]] = None,
    ) -> None:
        """Increment a counter metric.

        Args:
            name: Name of the metric
            value: Value to increment by
            tags: Optional tags/labels for the metric
        """
        counter = self._get_counter(name, tags)
        if tags:
            counter.labels(**tags).inc(value)
        else:
            counter.inc(value)

    async def gauge(
        self,
        name: str,
        value: MetricValue,
        tags: Optional[Dict[str, str]] = None,
    ) -> None:
        """Set a gauge metric.

        Args:
            name: Name of the metric
            value: Value to set
            tags: Optional tags/labels for the metric
        """
        gauge = self._get_gauge(name, tags)
        if tags:
            gauge.labels(**tags).set(value)
        else:
            gauge.set(value)

    async def histogram(
        self,
        name: str,
        value: MetricValue,
        tags: Optional[Dict[str, str]] = None,
        buckets: tuple[float, ...] = DEFAULT_DURATION_BUCKETS,
    ) -> None:
        """Record a histogram observation.

        Args:
            name: Name of the metric
            value: Value to observe
            tags: Optional tags/labels for the metric
            buckets: Histogram buckets
        """
        histogram = self._get_histogram(name, tags, buckets)
        if tags:
            histogram.labels(**tags).observe(value)
        else:
            histogram.observe(value)

    async def summary(
        self,
        name: str,
        value: MetricValue,
        tags: Optional[Dict[str, str]] = None,
    ) -> None:
        """Record a summary observation.

        Args:
            name: Name of the metric
            value: Value to observe
            tags: Optional tags/labels for the metric
        """
        summary = self._get_summary(name, tags)
        if tags:
            summary.labels(**tags).observe(value)
        else:
            summary.observe(value)

    def start_http_server(self, port: int = 8000, addr: str = "") -> None:
        """Start the Prometheus HTTP server to expose metrics.

        Args:
            port: Port to listen on
            addr: Address to bind to
        """
        prom.start_http_server(port, addr)
