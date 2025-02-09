"""Examples of using the gateway logging system.

Shows:
- Basic logging setup
- Customer/asset context
- High-volume logging
- Security logging
- Metrics logging
"""

import logging
from typing import Any, Optional

from .formatters import BaseFormatter, MetricsFormatter, SecurityFormatter
from .handlers.batch import BatchHandler
from .log_settings import LogComponent, LoggingConfig


def setup_basic_logging() -> None:
    """Basic logging setup example."""
    # Create and configure handler
    basic_handler = logging.StreamHandler()
    basic_handler.setFormatter(BaseFormatter(component=LogComponent.API))

    # Add handler to root logger
    logging.root.addHandler(basic_handler)
    logging.root.setLevel(logging.INFO)


def log_with_context(
    log_instance: logging.Logger,
    message: str,
    customer_id: str,
    asset_id: Optional[str] = None,
    **extra: Any,
) -> None:
    """Log with customer/asset context.

    Example:
        api_logger = logging.getLogger("gateway.api")
        log_with_context(
            api_logger,
            "API request processed",
            customer_id="cust123",
            asset_id="asset456",
            duration_ms=127,
            status_code=200
        )
    """
    extra_fields = {"customer_id": customer_id, "asset_id": asset_id or "unknown", **extra}

    log_instance.info(message, extra=extra_fields)


def setup_high_volume_logging(settings: LoggingConfig) -> None:
    """Setup logging for high-volume components."""
    # Create base handler
    protocol_handler = logging.FileHandler(settings.get_log_path(LogComponent.PROTOCOL))
    protocol_handler.setFormatter(BaseFormatter(component=LogComponent.PROTOCOL))

    # Wrap with batch handler
    batch_handler = BatchHandler(
        protocol_handler, batch_size=settings.batch_size, flush_interval=1.0, max_buffer=10000
    )

    # Configure logger
    protocol_logger = logging.getLogger("gateway.protocol")
    protocol_logger.addHandler(batch_handler)
    protocol_logger.setLevel(logging.INFO)


def setup_security_logging(settings: LoggingConfig) -> None:
    """Setup logging for security events."""
    auth_handler = logging.FileHandler(settings.get_log_path(LogComponent.AUTH))
    auth_handler.setFormatter(SecurityFormatter(component=LogComponent.AUTH))

    auth_logger = logging.getLogger("gateway.auth")
    auth_logger.addHandler(auth_handler)
    auth_logger.setLevel(logging.INFO)


def setup_metrics_logging(settings: LoggingConfig) -> None:
    """Setup logging for metrics collection."""
    # Create base handler
    metrics_file_handler = logging.FileHandler(settings.get_log_path(LogComponent.METRICS))
    metrics_file_handler.setFormatter(MetricsFormatter(component=LogComponent.METRICS))

    # Wrap with batch handler for performance
    metrics_batch_handler = BatchHandler(
        metrics_file_handler,
        batch_size=5000,  # Larger batches for metrics
        flush_interval=0.5,  # More frequent flushes
        max_buffer=50000,  # Larger buffer for spikes
    )

    metrics_logger = logging.getLogger("gateway.metrics")
    metrics_logger.addHandler(metrics_batch_handler)
    metrics_logger.setLevel(logging.INFO)


# Usage examples
if __name__ == "__main__":
    # Basic setup
    setup_basic_logging()
    example_logger = logging.getLogger("example")

    # Log with context
    log_with_context(
        example_logger,
        "Processing asset update",
        customer_id="cust123",
        asset_id="asset456",
        status="active",
    )

    # Setup for high volume
    app_settings = LoggingConfig(is_production=True)
    setup_high_volume_logging(app_settings)
    setup_security_logging(app_settings)
    setup_metrics_logging(app_settings)
