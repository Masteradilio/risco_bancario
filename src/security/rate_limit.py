"""Small in-process fixed-window limiter for the local API boundary."""

from __future__ import annotations

from collections import defaultdict, deque
from collections.abc import Callable
from threading import Lock
from time import monotonic


class RateLimitExceeded(RuntimeError):
    pass


class RateLimiter:
    def __init__(
        self, requests: int, window_seconds: int, clock: Callable[[], float] = monotonic
    ) -> None:
        self.requests = requests
        self.window_seconds = window_seconds
        self.clock = clock
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def check(self, key: str) -> None:
        now = self.clock()
        with self._lock:
            events = self._events[key]
            while events and events[0] <= now - self.window_seconds:
                events.popleft()
            if len(events) >= self.requests:
                raise RateLimitExceeded("rate limit exceeded")
            events.append(now)
