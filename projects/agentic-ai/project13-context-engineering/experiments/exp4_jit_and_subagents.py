"""EXPERIMENT 4 — don't carry what you can fetch (just-in-time retrieval) and don't hold what a helper can digest (sub-agents).
Run: python experiments/exp4_jit_and_subagents.py"""
from _common import table

from subagent import delegate
from tokens import count_text
from world import CODE, REGION, World

w = World()
corpus = sum(count_text(w.shard_text(n)) for n in range(1, w.total + 1))
rows = [("A. stuff all 100 shards in the prompt", f"{corpus:,}", "impossible: window is 30,000", "-")]

# B. just-in-time: let the agent SEARCH, then read only what it needs
w2 = World()
hits_code = w2.call("search_logs", {"query": "FACT:"})
hits_region = w2.call("search_logs", {"query": "USER-CONSTRAINT:"})
read = w2.call("read_log", {"shard": 3})
used = count_text(hits_code) + count_text(hits_region) + count_text(read)
found = CODE in hits_code and REGION in hits_region
rows.append(("B. search first, read one shard if needed", f"{used:,}", "correct" if found else "wrong", "2 searches + 1 read"))

# C. sub-agent: scan everything in its own window, hand back a tiny report
report, sub = delegate(World())
parent_ctx = count_text(report) + 200
rows.append(("C. sub-agent scans everything", f"parent sees {parent_ctx:,}", "correct" if CODE in report and REGION in report else "wrong",
             f"sub-agent bill {sub.billed_tokens:,} (its window peaked at {sub.peak_tokens:,})"))
table(rows, ["approach", "tokens in the PARENT's context", "result", "note"])
print(f"""
Report the sub-agent returned ({count_text(report)} tokens):
{report}

Lessons
* JIT retrieval (B) is the biggest win when you know what to look for: the corpus stays outside; the agent holds references (shard numbers, file paths) and pulls slices.
  The cost is that it needs a good search tool; a bad search = the agent never sees the thing it needed.
* A sub-agent (C) protects the PARENT's window and keeps noise out of it, but it still READ all {corpus:,} tokens, so total spend is not lower, and a 2-hop report can drop detail.
  Make the sub-agent return structured, verbatim facts and a pointer to where each came from, not a story.""")
