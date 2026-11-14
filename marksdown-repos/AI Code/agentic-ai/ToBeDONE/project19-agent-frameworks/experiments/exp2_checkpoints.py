"""EXPERIMENT 2 — checkpoints: crash recovery, the duplicate-side-effect trap, and time travel.
Run: python experiments/exp2_checkpoints.py"""
from _common import table, title

from miniflow import MemoryCheckpointer
from scenario import Shop, build_refund_graph

REQ = {"request": "refund ORD-1001 please"}

title("A. a transient failure in the LAST step (the email service times out)")
shop = Shop()
shop.fail = {"notify": 1}
app = build_refund_graph(shop).compile(MemoryCheckpointer())
r1 = app.invoke(REQ, thread="A")
print("first call :", r1.status, "|", r1.error, "| ran:", r1.ran)
print("money moved:", len(shop.ledger), "refund(s)   emails sent:", len(shop.outbox))
r2 = app.invoke(None, thread="A")                          # no input = 'continue this thread'
print("resume call:", r2.status, "| ran:", r2.ran, "| reply:", r2.state["reply"])
print("money moved:", len(shop.ledger), "refund(s)   emails sent:", len(shop.outbox), "  refund attempts:", shop.attempts["refund"])
print("-> the resume re-ran ONLY 'notify'. The earlier, expensive/irreversible steps were not repeated.")

title("B. the trap: the work happened, but the caller never heard (timeout AFTER the refund moved money)")
rows = []
for idem in (False, True):
    shop = Shop()
    shop.fail = {"refund_after": 1}
    app = build_refund_graph(shop, idempotent=idem).compile(MemoryCheckpointer())
    app.invoke(REQ, thread="B")
    r = app.invoke(None, thread="B")
    rows.append(("with idempotency key" if idem else "no idempotency key", r.status, f"{len(shop.ledger)} refund(s) in the ledger", shop.attempts["refund"]))
table(rows, ["variant", "final status", "money actually moved", "refund calls made"])
print("""
A checkpoint says 'node refund did not finish'. It cannot know that the payment provider DID take the action. On resume the node runs again.
Frameworks give you AT-LEAST-ONCE node execution, not exactly-once. Exactly-once is built from at-least-once plus an IDEMPOTENCY KEY
(same key -> the provider returns the first result instead of paying twice). This is the most important production lesson in this project.""")

title("C. time travel: look at history, fork from an earlier step with a patched state")
shop = Shop()
app = build_refund_graph(shop).compile(MemoryCheckpointer())
app.invoke(REQ, thread="C")
rows = [(c["step"], c["status"], ",".join(c["next"]) or "-", c["state"].get("order", {}) and c["state"]["order"]["amount"] or "-", len(c["state"]["log"])) for c in app.history("C")]
table(rows, ["step", "status", "runs next", "order amount", "log entries"])
before = len(shop.ledger)
step_lookup = next(c["step"] for c in app.history("C") if c["next"] == ["lookup"])
app.fork("C", step_lookup, "C-what-if", patch={"order_id": "ORD-1002"})
r = app.invoke(None, thread="C-what-if")
print(f"\nWHAT IF classify had extracted ORD-1002? forked at step {step_lookup} with order_id patched ...")
print("fork result:", r.status, "| ran:", r.ran, "|", r.interrupt["payload"]["question"] if r.interrupt else "")
print("original thread untouched:", app.cp.latest("C")["state"]["reply"], "| refunds:", before, "->", len(shop.ledger), "(the what-if is paused for approval, nothing paid)")
app.fork("C", step_lookup, "C-replay")
r = app.invoke(None, thread="C-replay")
print(f"\nREPLAY of the same request from step {step_lookup}: ran {r.ran} -> refunds in ledger: {len(shop.ledger)} (the idempotency key stopped a second payment) BUT emails sent: {len(shop.outbox)} - notify has no key, so the customer got two emails")
print("""
Notes: (1) the history shows step 4 twice: 'running' then 'done' - the status change is saved as its own record.
(2) A fork re-executes everything AFTER the chosen step, including side effects. Time travel is safe only if the nodes are idempotent
    or you fork before read-only steps. (3) classify and lookup were not re-run when forking later; the saved state was reused.""")
