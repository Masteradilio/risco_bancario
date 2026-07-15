"""Bounded executor for API batch jobs with explicit backpressure."""

from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor
from threading import BoundedSemaphore
from typing import Any


class BatchQueueFullError(RuntimeError):
    """Raised instead of silently growing an unbounded process queue."""


class BoundedBatchExecutor:
    def __init__(self, *, workers: int, queue_capacity: int) -> None:
        if workers <= 0 or queue_capacity < 0:
            raise ValueError("workers must be positive and queue capacity non-negative")
        self._executor = ThreadPoolExecutor(max_workers=workers, thread_name_prefix="ecl-job")
        self._slots = BoundedSemaphore(workers + queue_capacity)

    def submit(self, function: Callable[..., Any], /, *args: Any, **kwargs: Any) -> Future[Any]:
        if not self._slots.acquire(blocking=False):
            raise BatchQueueFullError("batch queue capacity exceeded")
        try:
            future = self._executor.submit(function, *args, **kwargs)
        except Exception:
            self._slots.release()
            raise
        future.add_done_callback(lambda _future: self._slots.release())
        return future

    def shutdown(self) -> None:
        self._executor.shutdown(wait=True, cancel_futures=False)
