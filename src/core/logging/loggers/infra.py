"""Infrastructure logging for database, cache, and other infrastructure components."""

import logging
from typing import Optional

from ..log_settings import LogComponent

# Basic logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),  # Log to console
        logging.FileHandler("infra.log"),  # Log to file
    ],
)


def get_infra_logger(
    name: Optional[str] = None,
    include_metrics: bool = True,
) -> logging.Logger:
    """Get logger for infrastructure components.

    Args:
        name: Optional sub-component name
        include_metrics: Whether to include metrics handler

    Returns:
        Configured logger instance
    """
    from . import get_logger_factory

    factory = get_logger_factory()
    logger = factory.get_logger(
        LogComponent.INFRA,
        use_syslog=True,  # Infrastructure logs should go to syslog
    )

    if name:
        logger = logging.getLogger(f"{logger.name}.{name}")
        logger.parent = logger

    return logger
