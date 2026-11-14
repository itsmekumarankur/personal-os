"""
The parallel building block.

Simply:
We have many tasks to run.
Instead of doing:

Task 1 → wait → Task 2 → wait → Task 3

we do:

Task 1 ─┐
Task 2 ─┼──> Run at the same time
Task 3 ─┘

This makes the overall work faster.
"""

import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any, Callable


# ---------------------------------------------------------
# Stores the result of ONE task.
#
# Simply:
# "Did it work? What did it return?
#  Did it fail? How much time did it take?"
# ---------------------------------------------------------
@dataclass
class Outcome:
    ok: bool                 # True = task succeeded, False = failed
    value: Any               # Result returned by the task
    error: str | None        # Error message if task failed
    seconds: float           # Time taken by the task


# ---------------------------------------------------------
# Runs the same function for many items in parallel.
#
# Example:
#
# items = ["Reviewer A", "Reviewer B", "Reviewer C"]
#
# Instead of:
#
# A → wait → B → wait → C
#
# We do:
#
# A ─┐
# B ─┼──> Run together
# C ─┘
# ---------------------------------------------------------
def parallel_map(
    fn: Callable,
    items: list,
    max_workers: int = 5
) -> list[Outcome]:

    # -----------------------------------------------------
    # This wrapper safely runs ONE item.
    #
    # Simply:
    # "Run the task, measure its time,
    #  and don't let an error crash everything."
    # -----------------------------------------------------
    def safe(item) -> Outcome:

        # Start stopwatch
        start = time.perf_counter()

        try:
            # Run the actual function
            value = fn(item)

            # Task succeeded
            return Outcome(
                True,                       # ok
                value,                      # result
                None,                       # no error
                time.perf_counter() - start # time taken
            )

        except Exception as e:
            # Task failed.
            # We store the error instead of crashing
            # the other parallel tasks.
            return Outcome(
                False,                                      # failed
                None,                                       # no result
                f"{type(e).__name__}: {e}"[:200],           # error message
                time.perf_counter() - start                 # time taken
            )

    # -----------------------------------------------------
    # If there is nothing to process, return empty result.
    # -----------------------------------------------------
    if not items:
        return []

    # -----------------------------------------------------
    # Create a pool of worker threads.
    #
    # max_workers = maximum number of tasks
    # that can run at the same time.
    #
    # Example:
    # max_workers = 3
    #
    # Task A ─┐
    # Task B ─┼──> 3 workers running together
    # Task C ─┘
    #
    # If there are only 2 items, we don't create 3 workers.
    # -----------------------------------------------------
    with ThreadPoolExecutor(
        max_workers=max(1, min(max_workers, len(items)))
    ) as pool:

        # -------------------------------------------------
        # Run safe(item) for every item in parallel.
        #
        # IMPORTANT:
        # pool.map() keeps the SAME ORDER as input.
        #
        # Input:
        # [A, B, C]
        #
        # Even if C finishes first:
        # C ──> finishes
        # A ──> finishes
        # B ──> finishes
        #
        # Result is still:
        # [result A, result B, result C]
        # -------------------------------------------------
        return list(pool.map(safe, items))