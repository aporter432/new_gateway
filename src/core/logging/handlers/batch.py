"""Batch logging handler for high-volume operations.

Features:
- Buffered writes for performance
- Async flushing
- Memory management
- Error handling
"""

import atexit
import logging
import threading
import time
from queue import Full, Queue
from typing import List


class BatchHandler(logging.Handler):
    """Handler that buffers records and writes in batches."""

    def __init__(
        self,
        target_handler: logging.Handler,
        batch_size: int = 1000,
        flush_interval: float = 1.0,
        max_buffer: int = 10000,
    ):
        """Initialize batch handler.

        Args:
            target_handler: Handler to write batched records to
            batch_size: Number of records to batch before writing
            flush_interval: Seconds between forced flushes
            max_buffer: Maximum records to buffer before forcing flush
        """
        super().__init__()
        self.target_handler = target_handler
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.max_buffer = max_buffer

        self._buffer: Queue = Queue(maxsize=max_buffer)
        self._last_flush = time.time()
        self._lock = threading.Lock()
        self._shutdown = threading.Event()

        # Start background flush thread
        self._flush_thread = threading.Thread(
            target=self._flush_loop, name="log-flusher", daemon=True
        )
        self._flush_thread.start()

        # Register shutdown handler
        atexit.register(self.close)

    def emit(self, record: logging.LogRecord) -> None:
        """Buffer record for batch processing.

        Args:
            record: Log record to buffer
        """
        try:
            # Force flush if buffer full
            if self._buffer.full():
                self.flush()

            self._buffer.put_nowait(record)

            # Flush if batch size reached
            if self._buffer.qsize() >= self.batch_size:
                self.flush()

        except (Full, IOError, OSError):
            # Handle queue full or IO-related errors
            self.handleError(record)

    def flush(self) -> None:
        """Flush buffered records to target handler."""
        with self._lock:
            try:
                records: List[logging.LogRecord] = []
                while not self._buffer.empty():
                    records.append(self._buffer.get_nowait())

                if records:
                    for record in records:
                        self.target_handler.handle(record)
                    self.target_handler.flush()

                self._last_flush = time.time()

            except (IOError, OSError) as e:
                # Handle IO-related errors
                if records:
                    # If we have records, use the first one for error context
                    self.handleError(records[0])
                else:
                    # Create a dummy record for error handling if no records available
                    dummy_record = logging.LogRecord(
                        name="batch_handler",
                        level=logging.ERROR,
                        pathname=__file__,
                        lineno=0,
                        msg=f"IO Error during flush: {str(e)}",
                        args=(),
                        exc_info=None,
                    )
                    self.handleError(dummy_record)

    def close(self) -> None:
        """Flush and close handler."""
        self._shutdown.set()
        self.flush()
        self.target_handler.close()
        super().close()

    def _flush_loop(self) -> None:
        """Background thread to periodically flush records."""
        while not self._shutdown.is_set():
            try:
                time_since_flush = time.time() - self._last_flush
                if time_since_flush >= self.flush_interval:
                    self.flush()
                time.sleep(0.1)  # Prevent tight loop
            except (IOError, OSError, RuntimeError) as e:
                # Handle IO errors and potential threading issues
                dummy_record = logging.LogRecord(
                    name="batch_handler",
                    level=logging.ERROR,
                    pathname=__file__,
                    lineno=0,
                    msg=f"Error in flush loop: {str(e)}",
                    args=(),
                    exc_info=None,
                )
                self.handleError(dummy_record)
