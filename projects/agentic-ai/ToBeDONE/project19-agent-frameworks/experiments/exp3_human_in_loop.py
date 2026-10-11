"""EXPERIMENT 3 — human in the loop: pause, survive a process exit, resume; and the 'code before interrupt runs twice' trap.
Run: python experiments/exp3_human_in_loop.py"""
import json
import os
import subprocess
import sys
import tempfile

from _common import title

from miniflow import END, Graph, MemoryCheckpointer, SqliteCheckpointer
from scenario import Shop, build_refund_graph

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")

if len(sys.argv) > 1 and sys.argv[1] == "--child":
    # This is a BRAND NEW PYTHON PROCESS: new Shop, new graph objects, nothing in memory. The only link to the past is the sqlite file.
    db, decision = sys.argv[2], sys.argv[3] == "approve"
    shop = Shop()
    app = build_refund_graph(shop).compile(SqliteCheckpointer(db))
    r = app.invoke(resume={"approve": decision, "who": "priya (manager)"}, thread="req-77")
    print(json.dumps({"status": r.status, "ran": r.ran, "reply": r.state.get("reply"), "approver": r.state.get("approver"), "refunds_in_this_process": len(shop.ledger)}))
    sys.exit(0)

title("A. pause for approval, exit the process, resume from a different process")
db = os.path.join(tempfile.mkdtemp(), "ckpt.sqlite")
shop = Shop()
app = build_refund_graph(shop).compile(SqliteCheckpointer(db))
r = app.invoke({"request": "refund ORD-1002 (laptop) please"}, thread="req-77")
print("process 1:", r.status, "| asked:", r.interrupt["payload"]["question"], "| nodes run:", r.ran)
print("          money moved so far:", len(shop.ledger), "| checkpoint rows in sqlite:", len(SqliteCheckpointer(db).history("req-77")))
print("process 1 now exits (imagine the manager answers tomorrow) ...")
for decision in ("approve",):
    out = subprocess.run([sys.executable, os.path.abspath(__file__), "--child", db, decision], capture_output=True, text=True, cwd=ROOT)
    print("process 2:", out.stdout.strip() or out.stderr.strip()[-300:])
print("-> the second process had no memory of the first; the checkpoint carried the state, the pending question and the position in the graph.")

title("B. the same request, manager says NO")
db2 = os.path.join(tempfile.mkdtemp(), "ckpt.sqlite")
app = build_refund_graph(Shop()).compile(SqliteCheckpointer(db2))
app.invoke({"request": "refund ORD-1002 (laptop) please"}, thread="req-77")
out = subprocess.run([sys.executable, os.path.abspath(__file__), "--child", db2, "deny"], capture_output=True, text=True, cwd=ROOT)
print("process 2:", out.stdout.strip() or out.stderr.strip()[-300:])

title("C. the trap: everything BEFORE ctx.interrupt() runs again on resume")
sent: list = []


def build(split: bool) -> Graph:
    g = Graph()
    if not split:
        def ask(s, ctx):
            sent.append("email: 'your request is being reviewed'")        # side effect BEFORE the interrupt
            a = ctx.interrupt("approve?")
            return {"ok": a}
        g.add_node("ask", ask).set_entry("ask").add_edge("ask", END)
    else:
        g.add_node("announce", lambda s: sent.append("email: 'your request is being reviewed'") or {})
        g.add_node("ask", lambda s, ctx: {"ok": ctx.interrupt("approve?")})
        g.set_entry("announce").add_edge("announce", "ask").add_edge("ask", END)
    return g


for split in (False, True):
    sent.clear()
    app = build(split).compile(MemoryCheckpointer())
    app.invoke({}, thread="x")
    app.invoke(resume=True, thread="x")
    print(("side effect in its own node :" if split else "side effect before interrupt:"), len(sent), "email(s) sent", sent)
print("""
Rule: a node that can pause must be SAFE TO RE-RUN. Put side effects in their own node BEFORE it (which is checkpointed and not repeated)
or after it. This is how LangGraph's interrupt() behaves too: the node restarts from the top.

Design questions for any approval step: Who can answer? How long may it wait? What happens at the timeout (deny by default)? Is the answer
recorded (state['approver'])? Can the answer be forged? (Here: no auth at all. In production the resume endpoint must authenticate and authorise the approver.)""")
