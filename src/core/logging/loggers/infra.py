"""Infrastructure logging for database, cache, and other infrastructure components."""

import logging

# Basic logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),  # Log to console
        logging.FileHandler("infra.log"),  # Log to file
    ],
)


def get_infra_logger(component: str = "") -> logging.Logger:
    """Get a logger for infrastructure components.

    Example:
        logger = get_infra_logger("redis")
        logger.info("Connected to Redis")
        logger.error("Failed to connect to database", exc_info=True)

    Args:
        component: The infrastructure component (e.g. "redis", "database")
    """
    name = "infra"
    if component:
        name = f"infra.{component}"

    return logging.getLogger(name)
