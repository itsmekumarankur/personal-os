"""A fixed-window rate limiter, one counter per caller. In memory, so it is per instance; with several
instances use the load balancer, an API gateway or Redis instead."""
import threading
import time


class RateLimiter:
    def __init__(self, limit: int, window_seconds: int = 60, clock=time.monotonic):
        self.limit, self.window, self._clock = limit, window_seconds, clock
        self._counts: dict[str, tuple[float, int]] = {}
        self._lock = threading.Lock()

    def check(self, key: str) -> tuple[bool, int]:
        """Returns (allowed, seconds_until_the_window_resets)."""
        now = self._clock()
        with self._lock:
            start, count = self._counts.get(key, (now, 0))
            if now - start >= self.window:
                start, count = now, 0
            count += 1
            self._counts[key] = (start, count)
            retry = max(1, int(self.window - (now - start)))
            return count <= self.limit, retry
