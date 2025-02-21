"""Logger factory for creating component-specific loggers."""

import logging
from typing import Optional

from metrics.backends.base import MetricsBackend

from ..handlers.file import get_file_handler
from ..handlers.metrics import get_metrics_handler
from ..handlers.stream import get_stream_handler
from ..handlers.syslog import get_syslog_handler
from ..log_settings import LogComponent, LoggingConfig


class LoggerFactory:
    """Factory for creating and configuring loggers."""

    _instance: Optional["LoggerFactory"] = None

    def __init__(self, config: LoggingConfig):
        """Initialize factory with configuration.

        Args:
            config: Logging configuration
        """
        self.config = config
        self._loggers: dict[str, logging.Logger] = {}

    def get_logger(
        self,
        component: LogComponent,
        *,
        use_file: bool = True,
        use_stream: bool = True,
        use_syslog: bool = False,
        metrics_backend: Optional[MetricsBackend] = None,
    ) -> logging.Logger:
        """Get or create a logger for a component.

        Args:
            component: Component to create logger for
            use_file: Whether to add file handler
            use_stream: Whether to add stream handler
            use_syslog: Whether to add syslog handler
            metrics_backend: Optional metrics backend

        Returns:
            Configured logger instance
        """
        logger_name = f"gateway.{component.value}"

        # Return existing logger if already configured
        if logger_name in self._loggers:
            return self._loggers[logger_name]

        # Create new logger
        logger = logging.getLogger(logger_name)
        logger_config = self.config.get_logger_config(component)

        # Set propagation
        logger.propagate = logger_config.propagate

        # Set level
        logger.setLevel(logging.getLevelName(logger_config.level))

        # Add handlers
        if use_file:
            logger.addHandler(get_file_handler(component, self.config))

        if use_stream:
            logger.addHandler(get_stream_handler(component, self.config))

        if use_syslog:
            logger.addHandler(get_syslog_handler(component, self.config))

        if metrics_backend is not None:
            logger.addHandler(get_metrics_handler(component, self.config, metrics_backend))

        # Store logger
        self._loggers[logger_name] = logger

        return logger

    def update_log_levels(self, level: str) -> None:
        """Update log level for all loggers.

        Args:
            level: New log level to set
        """
        for logger in self._loggers.values():
            logger.setLevel(logging.getLevelName(level))
            for handler in logger.handlers:
                handler.setLevel(logging.getLevelName(level))

    @classmethod
    def get_instance(cls, config: Optional[LoggingConfig] = None) -> "LoggerFactory":
        """Get or create singleton instance.

        Args:
            config: Optional configuration to use

        Returns:
            Logger factory instance
        """
        if cls._instance is None:
            if config is None:
                config = LoggingConfig()
            cls._instance = cls(config)
        return cls._instance


def get_logger_factory(config: Optional[LoggingConfig] = None) -> LoggerFactory:
    """Get or create global logger factory.

    Args:
        config: Optional configuration to use

    Returns:
        Logger factory instance
    """
    return LoggerFactory.get_instance(config)
