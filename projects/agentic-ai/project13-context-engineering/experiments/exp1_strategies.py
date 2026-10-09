"""EXPERIMENT 1 — nine ways to run a 100-step task in a 30k-token window. Who still knows the step-3 code at step 101?
Run: python experiments/exp1_strategies.py"""
from _common import spark, table

from agent import STRATEGIES, run

BUDGET = STRATEGIES["naive"].budget
rows, curves = [], []
for name in ["naive", "window", "clear_results", "clear_results+inputs", "summarize_lossy", "summarize_structured", "clear+ledger", "summarize_lossy+ledger", "clear+notes"]:
    r = run(name)
    verdict = "CORRECT" if r.correct else ("OVERFLOW" if r.overflow_at else "WRONG: " + r.answer[:34])
    rows.append((name, r.steps, f"{r.peak_tokens:,}", f"{r.billed_tokens:,}", len(r.events), verdict))
    curves.append((name, spark(r.curve, BUDGET)))
print(f"window budget = {BUDGET:,} tokens; management starts at 70%; each log shard is ~{run('naive', max_steps=2).curve[-1] // 2:,} tokens\n")
table(rows, ["strategy", "steps", "peak context", "input tokens billed", "edits", "final answer"])
print("\ncontext size over the run ('@' = the budget, one column ~ 2 steps)")
for n, s in curves:
    print(f"{n:24} |{s}|")
print("""
How to read this
* naive          grows until the window is full and the request is rejected (step ~25 of 100).
* window         stays small but forgot shards 3 and 7 long ago -> 'not in my context'. It is honest; a confabulating model would guess (see exp2).
* clear_results  same story: the facts lived ONLY inside tool results, and those were cleared. Clearing is great for noise, fatal for unrecorded facts.
* summarize_lossy the summary says 'an approval code was encountered' but not WHICH one. This is the most common real-world failure.
* summarize_structured / ledger / notes keep exact values because something wrote them down OUTSIDE the stuff being thrown away.
Cost: 'input tokens billed' is the sum of every prompt sent. Long tasks are quadratic: each step re-sends the whole context. Management lowers the peak; caching lowers the price (exp3).""")
