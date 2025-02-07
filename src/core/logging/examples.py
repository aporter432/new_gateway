"""Examples of using the gateway logging system.

Shows:
- Basic logging setup
- Customer/asset context
- High-volume logging
- Security logging
- Metrics logging
"""

import logging
from typing import Optional

from .formatters import GatewayFormatter, MetricsFormatter, SecurityFormatter
from .handlers.batch import BatchHandler
from .log_settings import LogComponent, LoggingConfig


def setup_basic_logging() -> None:
    """Basic logging setup example."""
    # Create and configure handler
    handler = logging.StreamHandler()
    handler.setFormatter(GatewayFormatter())

    # Add handler to root logger
    logging.root.addHandler(handler)
    logging.root.setLevel(logging.INFO)


def log_with_context(
    logger: logging.Logger,
    message: str,
    customer_id: str,
    asset_id: Optional[str] = None,
    **extra: Any,
) -> None:
    """Log with customer/asset context.

    Example:
        logger = logging.getLogger("gateway.api")
        log_with_context(
            logger,
            "API request processed",
            customer_id="cust123",
            asset_id="asset456",
            duration_ms=127,
            status_code=200
        )
    """
    extra_fields = {"customer_id": customer_id, "asset_id": asset_id or "unknown", **extra}

    logger.info(message, extra=extra_fields)


def setup_high_volume_logging(config: LoggingConfig) -> None:
    """Setup logging for high-volume components."""
    # Create base handler
    base_handler = logging.FileHandler(config.get_log_path(LogComponent.PROTOCOL))
    base_handler.setFormatter(GatewayFormatter())

    # Wrap with batch handler
    batch_handler = BatchHandler(
        base_handler, batch_size=config.batch_size, flush_interval=1.0, max_buffer=10000
    )

    # Configure logger
    logger = logging.getLogger("gateway.protocol")
    logger.addHandler(batch_handler)
    logger.setLevel(logging.INFO)


def setup_security_logging(config: LoggingConfig) -> None:
    """Setup logging for security events."""
    handler = logging.FileHandler(config.get_log_path(LogComponent.AUTH))
    handler.setFormatter(SecurityFormatter())

    logger = logging.getLogger("gateway.auth")
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def setup_metrics_logging(config: LoggingConfig) -> None:
    """Setup logging for metrics collection."""
    # Create base handler
    base_handler = logging.FileHandler(config.get_log_path(LogComponent.METRICS))
    base_handler.setFormatter(MetricsFormatter())

    # Wrap with batch handler for performance
    metrics_handler = BatchHandler(
        base_handler,
        batch_size=5000,  # Larger batches for metrics
        flush_interval=0.5,  # More frequent flushes
        max_buffer=50000,  # Larger buffer for spikes
    )

    logger = logging.getLogger("gateway.metrics")
    logger.addHandler(metrics_handler)
    logger.setLevel(logging.INFO)


# Usage examples
if __name__ == "__main__":
    # Basic setup
    setup_basic_logging()
    logger = logging.getLogger("example")

    # Log with context
    log_with_context(
        logger,
        "Processing asset update",
        customer_id="cust123",
        asset_id="asset456",
        status="active",
    )

    # Setup for high volume
    config = LoggingConfig(is_production=True)
    setup_high_volume_logging(config)
    setup_security_logging(config)
    setup_metrics_logging(config)
