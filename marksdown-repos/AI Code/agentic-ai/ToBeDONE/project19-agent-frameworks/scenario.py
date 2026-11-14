"""The shared business scenario: a customer-support refund desk.  Used by every experiment, in three shapes:
   (a) a GRAPH WORKFLOW  (deterministic path with a human approval step)           -> build_refund_graph
   (b) a TEAM OF AGENTS  (triage hands off to specialists)                        -> build_agents + FakeSupportModel
   (c) a HAND-ROLLED function (no framework, for comparison)                      -> raw_refund
Money and email are REAL side effects here (a ledger and an outbox) so you can see duplicates, not just read about them."""
import json
import re

from miniflow import END, Agent, Graph, append, overwrite  # noqa: F401

ORDERS = {
    "ORD-1001": {"item": "headphones", "amount": 59.0, "customer": "asha"},
    "ORD-1002": {"item": "laptop", "amount": 240.0, "customer": "ravi"},
    "ORD-1003": {"item": "cable", "amount": 12.5, "customer": "mei"},
}


class Shop:
    """Pretend payment provider + mailer. Everything it does is recorded so experiments can count side effects."""

    def __init__(self):
        self.ledger: list = []            # money actually moved
        self.outbox: list = []            # emails actually sent
        self._keys: dict = {}
        self.attempts = {"refund": 0, "email": 0}
        self.fail = {}                    # e.g. {"notify": 1} -> the next notify raises once;  {"refund_after": 1} -> money moves, THEN the call raises

    def _maybe_fail(self, what, after=False):
        key = what + ("_after" if after else "")
        if self.fail.get(key, 0) > 0:
            self.fail[key] -= 1
            raise TimeoutError(f"{what} timed out")

    def refund(self, order_id: str, amount: float, idempotency_key: str | None = None) -> str:
        self.attempts["refund"] += 1
        if idempotency_key and idempotency_key in self._keys:         # what real payment APIs (e.g. Stripe-style) offer: same key => same result, no second payment
            return self._keys[idempotency_key]
        self._maybe_fail("refund")
        rid = f"RF-{len(self.ledger) + 1}"
        self.ledger.append({"id": rid, "order": order_id, "amount": amount})
        if idempotency_key:
            self._keys[idempotency_key] = rid
        self._maybe_fail("refund", after=True)                        # the nasty case: the work happened, the caller never found out
        return rid

    def email(self, to: str, body: str):
        self.attempts["email"] += 1
        self._maybe_fail("notify")
        self.outbox.append({"to": to, "body": body})


# ----------------------------------------------------------------------------- (a) graph workflow
def build_refund_graph(shop: Shop, idempotent: bool = True, threshold: float = 100.0) -> Graph:
    g = Graph(reducers={"log": append}, defaults={"log": []})

    def classify(s):
        m = re.search(r"ORD-\d+", s["request"])
        intent = "refund" if re.search(r"refund|money back", s["request"], re.I) else "other"
        return {"order_id": m.group(0) if m else None, "intent": intent, "log": ["classified"]}

    def lookup(s):
        o = ORDERS.get(s.get("order_id") or "")
        return {"order": o, "log": ["looked up order"]}

    def approve(s, ctx):
        # NOTE: everything above ctx.interrupt() runs AGAIN when the run resumes. Keep this node free of side effects.
        answer = ctx.interrupt({"question": f"Approve refund of {s['order']['amount']} for {s['order_id']}?", "amount": s["order"]["amount"]})
        return {"approved": bool(answer.get("approve")), "approver": answer.get("who"), "log": [f"human said {answer.get('approve')}"]}

    def refund(s):
        key = f"refund:{s['order_id']}" if idempotent else None
        rid = shop.refund(s["order_id"], s["order"]["amount"], key)
        return {"refund_id": rid, "log": [f"refunded {rid}"]}

    def notify(s):
        shop.email(s["order"]["customer"], f"Refund {s['refund_id']} issued for {s['order_id']}")
        return {"log": ["notified"], "reply": f"Refund {s['refund_id']} issued."}

    def reply_error(s):
        return {"reply": "Sorry, I could not find that order or understand the request.", "log": ["error reply"]}

    def reply_denied(s):
        return {"reply": "A manager declined this refund.", "log": ["denied reply"]}

    for n, f in [("classify", classify), ("lookup", lookup), ("approve", approve), ("refund", refund), ("notify", notify),
                 ("reply_error", reply_error), ("reply_denied", reply_denied)]:
        g.add_node(n, f)
    g.set_entry("classify").add_edge("classify", "lookup")
    g.add_conditional("lookup", lambda s: "reply_error" if not s.get("order") or s["intent"] != "refund" else ("approve" if s["order"]["amount"] > threshold else "refund"))
    g.add_conditional("approve", lambda s: "refund" if s.get("approved") else "reply_denied")
    g.add_edge("refund", "notify").add_edge("notify", END).add_edge("reply_error", END).add_edge("reply_denied", END)
    return g


# ----------------------------------------------------------------------------- (c) hand-rolled
def raw_refund(shop: Shop, request: str, approve_fn=None) -> str:
    """The same business logic as a plain function. Short, readable, fast to write. What it cannot do: pause for hours, survive a crash
    without starting over, show its steps, or be forked. (exp5 tries each of these.)"""
    m = re.search(r"ORD-\d+", request)
    order = ORDERS.get(m.group(0)) if m else None
    if not order or not re.search(r"refund|money back", request, re.I):
        return "Sorry, I could not find that order or understand the request."
    if order["amount"] > 100 and not (approve_fn and approve_fn(order)):
        return "A manager declined this refund."
    rid = shop.refund(m.group(0), order["amount"], f"refund:{m.group(0)}")
    shop.email(order["customer"], f"Refund {rid} issued for {m.group(0)}")
    return f"Refund {rid} issued."


# ----------------------------------------------------------------------------- (b) team of agents
def build_agents(shop: Shop, ping_pong: bool = False):
    def lookup_order(order_id: str) -> str:
        """Look up an order by id."""
        o = ORDERS.get(order_id)
        return json.dumps({"order_id": order_id, **o}) if o else "NOT_FOUND"

    def issue_refund(order_id: str, amount: float) -> str:
        """Refund an order."""
        return shop.refund(order_id, amount, f"refund:{order_id}")

    def get_invoice(order_id: str) -> str:
        """Fetch the invoice for an order."""
        o = ORDERS.get(order_id)
        return f"Invoice for {order_id}: {o['amount']} for {o['item']}; billed to {o['customer']}@example.com" if o else "NOT_FOUND"

    triage = Agent("triage", "Route the customer to the right specialist. Never solve problems yourself.")
    refunds = Agent("refunds", "Handle refund requests. Look up the order, then refund it.", {"lookup_order": lookup_order, "issue_refund": issue_refund})
    billing = Agent("billing", "Answer invoice questions.", {"get_invoice": get_invoice})
    triage.handoffs = [refunds, billing]
    if ping_pong:
        refunds.handoffs = [triage]
    return triage, refunds, billing


def _calls(messages):
    """Pair every tool_use with its result: [(name, input, result_text, is_error)]."""
    uses, out = {}, []
    for m in messages:
        if m["role"] == "assistant":
            for b in m["content"]:
                if b["type"] == "tool_use":
                    uses[b["id"]] = b
        elif isinstance(m["content"], list):
            for r in m["content"]:
                if r.get("type") == "tool_result" and r["tool_use_id"] in uses:
                    u = uses[r["tool_use_id"]]
                    out.append((u["name"], u["input"], r["content"], bool(r.get("is_error"))))
    return out


class FakeSupportModel:
    """Scripted 'LLM' for the agent team. Like Project 13's fake: its behaviour depends ONLY on what is visible in the messages and on which agent is active."""

    def __init__(self, ping_pong=False, overreach=False, leak_email=False):
        self.ping_pong, self.overreach, self.leak = ping_pong, overreach, leak_email

    def __call__(self, agent, messages):
        user = messages[0]["content"]
        calls = _calls(messages)
        tid = f"tu_{len(messages)}"
        tool = lambda name, **inp: [{"type": "tool_use", "id": tid, "name": name, "input": inp}]      # noqa: E731
        text = lambda t: [{"type": "text", "text": t}]                                                # noqa: E731
        oid = (re.search(r"ORD-\d+", user) or [None])[0]
        if agent.name == "triage":
            if self.overreach and not calls:
                return tool("admin_override", order_id=oid or "ORD-1001")                           # triage tries a tool it does not own
            if self.ping_pong:
                return tool("transfer_to_refunds")
            if re.search(r"refund|money back", user, re.I):
                return tool("transfer_to_refunds")
            if re.search(r"invoice|bill", user, re.I):
                return tool("transfer_to_billing")
            return text("I can help with refunds and invoices. What do you need?")
        if agent.name == "refunds":
            if self.ping_pong:
                return tool("transfer_to_triage")
            names = [c[0] for c in calls if not c[0].startswith("transfer_to_")]
            if "lookup_order" not in names:
                return tool("lookup_order", order_id=oid or "")
            lk = next(c for c in calls if c[0] == "lookup_order")
            if lk[2] == "NOT_FOUND":
                return text("I could not find that order.")
            if "issue_refund" not in names:
                return tool("issue_refund", order_id=oid, amount=json.loads(lk[2])["amount"])
            ir = next(c for c in calls if c[0] == "issue_refund")
            return text("This refund needs a manager's approval; I have escalated it." if ir[3] else f"Done: refund {ir[2]} issued.")
        if agent.name == "billing":
            if not any(c[0] == "get_invoice" for c in calls):
                return tool("get_invoice", order_id=oid or "")
            inv = next(c for c in calls if c[0] == "get_invoice")[2]
            return text(inv if self.leak else inv.split(";")[0])
        return text("?")


# ----------------------------------------------------------------------------- guardrails and hooks (plain functions)
def injection_guard(text: str):
    if re.search(r"ignore (all |your )?(previous|prior) instructions|system prompt", text, re.I):
        return "looks like a prompt-injection attempt"


def pii_guard(text: str):
    if re.search(r"[\w.]+@[\w.]+\.\w+", text):
        return "output contains an email address"


def refund_limit(agent_name: str, tool_name: str, args: dict, limit: float = 100.0):
    if tool_name == "issue_refund" and float(args.get("amount", 0)) > limit:
        return f"refunds over {limit:g} need human approval (tried {args['amount']})"
