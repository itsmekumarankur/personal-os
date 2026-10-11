"""EXPERIMENT 3 — context editing vs prompt caching. Every edit to an EARLIER part of the prompt breaks the cached prefix.
Run: python experiments/exp3_cache.py"""
from _common import table

from agent import run

rows = []
for name in ["naive", "clear_eager", "clear_results", "clear_batch", "summarize_structured"]:
    r = run(name, max_steps=60) if name == "naive" else run(name)
    cost_nocache = r.billed_tokens
    rows.append((name, r.steps, r.prefix_breaks, f"{cost_nocache:,}", f"{r.cached_cost_units:,.0f}", f"{r.cached_cost_units / cost_nocache:.2f}", "ok" if r.correct else "-"))
table(rows, ["strategy", "steps", "prefix breaks", "cost, no cache", "cost, with cache", "ratio", "answer"])
print("""
Units: 1.0 per input token without caching; with a moving breakpoint the unchanged prefix costs 0.1 and everything after the first change costs 1.25 (re-written).
* append-only (naive, up to its overflow) keeps the prefix intact: each step re-reads the old prompt at 0.1.
* clear_eager edits a little EVERY step once the threshold is hit -> the prefix changes every step -> it pays the write price again and again.
* clear_batch waits, then clears a LOT at once (down to 30%), so the next ~dozens of steps are append-only again. Fewer breaks, much cheaper.
Lesson (also in Anthropic's context-editing docs): use a threshold and a minimum amount to clear per edit ('clear_at_least'), so each edit is worth the cache rewrite.""")
