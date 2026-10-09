"""Who called what, and what happened. Written for every decision, including the refusals."""
import json
import threading
import time
from collections import defaultdict, deque


class AuditLog:
    def __init__(self, path: str | None = None, keep: int = 1000):
        self.path, self.rows, self._lock = path, deque(maxlen=keep), threading.Lock()

    def record(self, **row):
        row = {"ts": round(time.time(), 3), **row}
        with self._lock:
            self.rows.append(row)
            if self.path:
                with open(self.path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(row, default=str) + "\n")

    def all(self):
        with self._lock:
            return list(self.rows)


class RateLimiter:
    """Sliding window per client: at most `limit` calls in any 60 seconds."""

    def __init__(self, limit: int, window: float = 60.0, clock=time.monotonic):
        self.limit, self.window, self.clock = limit, window, clock
        self.hits = defaultdict(deque)
        self._lock = threading.Lock()

    def allow(self, key: str) -> bool:
        now = self.clock()
        with self._lock:
            q = self.hits[key]
            while q and now - q[0] >= self.window:
                q.popleft()
            if len(q) >= self.limit:
                return False
            q.append(now)
            return True
