"""EXPERIMENT 5 — do you even need a framework?  The same refund logic as a plain function and as a graph; then ask each one to do hard things.
Run: python experiments/exp5_framework_or_not.py"""
import inspect

from _common import table, title

import scenario
from miniflow import MemoryCheckpointer
from scenario import Shop, build_refund_graph, raw_refund

REQS = ["refund ORD-1001 please", "refund ORD-1003 please", "refund ORD-9999 please", "hello"]

title("A. same behaviour on easy inputs")
rows = []
for q in REQS:
    s1, s2 = Shop(), Shop()
    a = raw_refund(s1, q)
    b = build_refund_graph(s2).compile(MemoryCheckpointer()).invoke({"request": q}, thread="x").state["reply"]
    rows.append((q, a == b, a))
table(rows, ["request", "identical reply", "reply"])
raw_loc = len([ln for ln in inspect.getsource(raw_refund).splitlines() if ln.strip() and not ln.strip().startswith(("#", '"""'))])
graph_loc = len([ln for ln in inspect.getsource(scenario.build_refund_graph).splitlines() if ln.strip() and not ln.strip().startswith("#")])
print(f"\nlines of code (rough): hand-rolled function {raw_loc},  graph definition {graph_loc}  (+ ~400 lines of miniflow, or a dependency in real life)")

title("B. now ask for things a function cannot do")
rows = []

# 1. email service fails after the refund
s = Shop()
s.fail = {"notify": 1}
try:
    raw_refund(s, REQS[0])
except TimeoutError:
    pass
raw_second = raw_refund(s, REQS[0])
s2 = Shop()
s2.fail = {"notify": 1}
app = build_refund_graph(s2).compile(MemoryCheckpointer())
app.invoke({"request": REQS[0]}, thread="t")
app.invoke(None, thread="t")
rows.append(("retry after a failure in step 4 of 4", f"re-ran everything: {s.attempts['refund']} refund calls", f"re-ran only the failed step: {s2.attempts['refund']} refund call"))

# 2. wait for a human
rows.append(("wait a day for a manager, process restarts", "needs a blocking callback (lost on restart) or you build your own state table", "built in: state saved, resume from any process (exp3)"))
# 3. see what happened
rows.append(("show the steps that ran, with timings", "add logging by hand in every step", "trace + checkpoint history for free (exp1, exp2)"))
# 4. what-if
rows.append(("replay from the middle with a changed value", "re-run from the start and hope inputs match", "fork(thread, step, patch=...) (exp2)"))
# 5. parallel
rows.append(("two branches in parallel, merge safely", "threads + locks + your own merge code", "supersteps + reducers (exp1 C)"))
table(rows, ["requirement", "plain function", "graph framework"])
print("(only the first row is measured here; the others are descriptions, each demonstrated for the graph side in exp1-3.)")

title("C. and the costs the table does not show")
print("""* A new vocabulary (nodes, edges, reducers, checkpoints) that every teammate must learn before they can debug anything.
* Your state must be serialisable (JSON). Open DB connections, clients, file handles and lambdas cannot live in state.
* The framework's abstractions leak: you still need idempotency (exp2), safe-to-rerun nodes (exp3), step limits (exp1).
* Lock-in and churn: frameworks change fast; upgrades can change behaviour. Keep business logic in plain functions and make the
  graph a thin wiring layer, so you could swap it. (In scenario.py the Shop is plain Python; nodes only call it.)
* Debugging goes through the framework's stack frames.

DECISION GUIDE
  linear, short, one process, no pauses             -> a function or a simple loop (Project 1). Do not add a framework.
  needs pause/resume, retries of one step, audit    -> a graph runtime with checkpoints (build or adopt).
  model decides the path, tools vary                -> an agent loop (Project 17's loop); add a framework only for tracing/sessions/guardrails you do not want to write.
  several specialists with different tools          -> handoffs, but first try ONE agent with a good tool set. Add agents when prompts or tools start conflicting.
  long-running + many users                         -> you need durable checkpoints, a queue, auth on resume: that is where frameworks earn their keep.""")
