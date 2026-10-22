"""In-process sliding-window rate limiter for low-volume public endpoints.

Login rate limiting is database-backed (see app.services.auth) so it works across workers.
This limiter is per process: with several workers or hosts, replace it with a shared store
(e.g. Redis) or rate limiting at the edge.
"""

import time
from collections import defaultdict, deque
from threading import Lock

from app.core.errors import AppError


class SlidingWindowLimiter:
    def __init__(self, max_hits: int, window_seconds: float) -> None:
        self.max_hits, self.window = max_hits, window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def hit(self, key: str) -> None:
        """Record one hit for `key`; raise 429 if the window is already full."""
        now = time.monotonic()
        with self._lock:
            q = self._hits[key]
            while q and now - q[0] > self.window:
                q.popleft()
            if len(q) >= self.max_hits:
                raise AppError(429, "rate_limited", "Too many submissions. Please try again later.")
            q.append(now)
