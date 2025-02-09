"""System metrics collection."""

import asyncio
import os
from typing import Optional

import psutil

from ..backends.base import MetricsBackend
from ..exceptions import SystemMetricsError


class SystemMetrics:
    """Collector for system-level metrics."""

    def __init__(
        self,
        backend: MetricsBackend,
        collection_interval: float = 15.0,
        process_id: Optional[int] = None,
    ):
        """Initialize system metrics collector.

        Args:
            backend: Metrics storage backend
            collection_interval: How often to collect metrics in seconds
            process_id: Optional specific process ID to monitor (defaults to current)

        Raises:
            SystemMetricsError: If initialization fails
        """
        try:
            from core.logging.loggers import get_system_logger

            self.backend = backend
            self.collection_interval = collection_interval
            self.process = psutil.Process(process_id or os.getpid())
            self._task: Optional[asyncio.Task] = None
            self.logger = get_system_logger("metrics")
        except (psutil.Error, OSError) as e:
            raise SystemMetricsError(
                f"Failed to initialize system metrics collector: {str(e)}",
                SystemMetricsError.INIT_FAILED,
            ) from e

    async def start(self) -> None:
        """Start collecting system metrics."""
        if self._task is not None:
            return

        self._task = asyncio.create_task(self._collect_metrics())
        self.logger.info(
            "System metrics collector started",
            extra={
                "collector_id": id(self),
                "collection_interval": self.collection_interval,
                "process_id": self.process.pid,
            },
        )

    async def stop(self) -> None:
        """Stop collecting system metrics."""
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
            self.logger.info(
                "System metrics collector stopped",
                extra={
                    "collector_id": id(self),
                    "process_id": self.process.pid,
                },
            )

    async def _collect_process_io_metrics(self) -> None:
        """Collect process IO metrics if available.

        Raises:
            SystemMetricsError: If IO metrics collection fails
        """
        try:
            io_counters = self.process.io_counters()  # type: ignore
            await self.backend.gauge("process_io_read_bytes", io_counters.read_bytes)
            await self.backend.gauge("process_io_write_bytes", io_counters.write_bytes)
        except (psutil.AccessDenied, AttributeError) as e:
            # IO counters not available on this platform or access denied
            raise SystemMetricsError(
                f"IO metrics unavailable: {str(e)}", SystemMetricsError.IO_UNAVAILABLE
            ) from e
        except Exception as e:
            self.logger.error(
                "Error collecting IO metrics",
                extra={
                    "error": str(e),
                    "collector_id": id(self),
                    "process_id": self.process.pid,
                },
            )
            raise SystemMetricsError(
                f"Failed to collect IO metrics: {str(e)}", SystemMetricsError.COLLECTION_FAILED
            ) from e

    async def _collect_metrics(self) -> None:
        """Collect system metrics at regular intervals."""
        while True:
            try:
                # Process metrics
                with self.process.oneshot():
                    try:
                        cpu_percent = self.process.cpu_percent()
                        memory_info = self.process.memory_info()
                        num_threads = self.process.num_threads()
                        try:
                            num_fds = self.process.num_fds()
                        except (psutil.AccessDenied, AttributeError) as e:
                            self.logger.warning(
                                "File descriptor metrics unavailable",
                                extra={
                                    "error": str(e),
                                    "collector_id": id(self),
                                    "process_id": self.process.pid,
                                },
                            )
                            num_fds = 0
                    except psutil.AccessDenied as e:
                        raise SystemMetricsError(
                            f"Permission denied accessing process metrics: {str(e)}",
                            SystemMetricsError.PERMISSION_DENIED,
                        ) from e
                    except psutil.NoSuchProcess as e:
                        raise SystemMetricsError(
                            f"Process not found: {str(e)}", SystemMetricsError.RESOURCE_NOT_FOUND
                        ) from e

                # Record process metrics
                await self.backend.gauge("process_cpu_percent", cpu_percent)
                await self.backend.gauge("process_memory_rss_bytes", memory_info.rss)
                await self.backend.gauge("process_memory_vms_bytes", memory_info.vms)
                await self.backend.gauge("process_threads", num_threads)
                if num_fds > 0:
                    await self.backend.gauge("process_fds", num_fds)

                # Collect IO metrics separately
                try:
                    await self._collect_process_io_metrics()
                except SystemMetricsError as e:
                    if e.error_code == SystemMetricsError.IO_UNAVAILABLE:
                        # Log but continue if IO metrics are unavailable
                        self.logger.warning(
                            "IO metrics collection skipped",
                            extra={
                                "error": str(e),
                                "collector_id": id(self),
                                "process_id": self.process.pid,
                            },
                        )
                    else:
                        raise

                # System-wide metrics
                try:
                    cpu_percent = psutil.cpu_percent(interval=None)
                    memory = psutil.virtual_memory()
                    disk = psutil.disk_usage("/")
                except (psutil.Error, OSError) as e:
                    raise SystemMetricsError(
                        f"System metrics unavailable: {str(e)}",
                        SystemMetricsError.SYSTEM_UNAVAILABLE,
                    ) from e

                # Record system metrics
                await self.backend.gauge("system_cpu_percent", cpu_percent)
                await self.backend.gauge("system_memory_used_bytes", memory.used)
                await self.backend.gauge("system_memory_total_bytes", memory.total)
                await self.backend.gauge("system_disk_used_bytes", disk.used)
                await self.backend.gauge("system_disk_total_bytes", disk.total)

                self.logger.debug(
                    "System metrics collected",
                    extra={
                        "collector_id": id(self),
                        "process_id": self.process.pid,
                        "metrics": {
                            "cpu_percent": cpu_percent,
                            "memory_used": memory.used,
                            "disk_used": disk.used,
                        },
                    },
                )

            except SystemMetricsError as e:
                self.logger.error(
                    "Error collecting system metrics",
                    extra={
                        "error": str(e),
                        "error_code": e.error_code,
                        "collector_id": id(self),
                        "process_id": self.process.pid,
                    },
                )

            except (psutil.Error, OSError, asyncio.CancelledError) as e:
                self.logger.error(
                    "Unexpected error collecting system metrics",
                    extra={
                        "error": str(e),
                        "collector_id": id(self),
                        "process_id": self.process.pid,
                    },
                )

            await asyncio.sleep(self.collection_interval)
