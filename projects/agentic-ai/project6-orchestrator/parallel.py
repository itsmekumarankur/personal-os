"""The parallel building block.

Follows the parallel() helper in Anthropic's claude-cookbooks
(patterns/agents/basic_workflows.ipynb): a thread pool with a worker cap, one
task per input, results returned in input order.

Added here: every task runs inside a wrapper that catches errors and measures
its own time, so one failing call cannot throw away the other results.
"""
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class Outcome:
    ok: bool
    value: Any
    error: str | None
    seconds: float


def parallel_map(fn: Callable, items: list, max_workers: int = 5) -> list[Outcome]:
    """Run fn(item) for every item at the same time (up to max_workers).

    The returned list lines up with `items`: outcome i belongs to item i.
    """
    def safe(item) -> Outcome:
        start = time.perf_counter()
        try:
            value = fn(item)
            return Outcome(True, value, None, time.perf_counter() - start)
        except Exception as e:  # noqa: BLE001 - isolate failures on purpose
            return Outcome(False, None, f"{type(e).__name__}: {e}"[:200], time.perf_counter() - start)

    if not items:
        return []
    with ThreadPoolExecutor(max_workers=max(1, min(max_workers, len(items)))) as pool:
        return list(pool.map(safe, items))   # map() keeps input order
