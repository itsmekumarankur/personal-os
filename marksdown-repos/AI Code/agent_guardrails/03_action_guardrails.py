"""
03 ACTION GUARDRAILS  -  "even if the tool call is valid, SHOULD this side-effect happen?"

Tool guardrails check the call is well-formed. Action guardrails check the CONSEQUENCE:
  - risk tiers      small & reversible -> auto;  medium -> human approval;  huge/forbidden -> blocked
  - hard limits     per-order value, daily cumulative value (a loop must not drain an account)
  - business rules  market hours, approved symbols, registered beneficiary only
  - idempotency     the same request retried (network glitch, agent loop) must not execute twice
  - dry-run         show what WOULD happen first (also great for testing a new agent safely)
  - compensation    every executed action records how to UNDO it

Run: python 03_action_guardrails.py
"""
from enum import Enum

PRICES = {"INFY": 1500.0, "TCS": 4000.0, "HDFCBANK": 1650.0}
AUTO_LIMIT, APPROVAL_LIMIT, DAILY_LIMIT = 20_000.0, 200_000.0, 250_000.0
MARKET_HOURS = range(9, 16)           # 09:00-15:59


class Decision(Enum):
    AUTO = "AUTO-EXECUTE"
    APPROVAL = "NEEDS HUMAN APPROVAL"
    BLOCK = "BLOCKED"


class ActionGate:
    def __init__(self):
        self.daily_notional = 0.0
        self.seen_keys = {}
        self.undo_log = []

    def evaluate(self, order):
        qty, sym = order["qty"], order["symbol"]
        value = qty * PRICES[sym]
        if order["hour"] not in MARKET_HOURS:
            return Decision.BLOCK, f"market closed at {order['hour']}:00", value
        if value <= 0:
            return Decision.BLOCK, "non-positive value", value
        if value > APPROVAL_LIMIT:
            return Decision.BLOCK, f"value {value:,.0f} above hard cap {APPROVAL_LIMIT:,.0f}", value
        if self.daily_notional + value > DAILY_LIMIT:
            return Decision.BLOCK, f"daily limit {DAILY_LIMIT:,.0f} would be exceeded (used {self.daily_notional:,.0f})", value
        if value > AUTO_LIMIT:
            return Decision.APPROVAL, f"value {value:,.0f} above auto limit {AUTO_LIMIT:,.0f}", value
        return Decision.AUTO, "within auto limit", value

    def submit(self, order, dry_run=False):
        key = order["idempotency_key"]
        if key in self.seen_keys:
            return f"DUPLICATE ignored (key {key} already executed -> {self.seen_keys[key]})"
        decision, why, value = self.evaluate(order)
        if decision is Decision.BLOCK:
            return f"{decision.value}: {why}"
        if decision is Decision.APPROVAL:
            return f"{decision.value}: {why} -> parked in approval queue (see 06_human_guardrails.py)"
        if dry_run:
            return f"DRY-RUN ok: would BUY {order['qty']} {order['symbol']} for {value:,.0f}. Nothing executed."
        self.daily_notional += value
        self.seen_keys[key] = f"order#{len(self.seen_keys) + 1}"
        self.undo_log.append(f"SELL {order['qty']} {order['symbol']} (compensates {key})")
        return f"EXECUTED {self.seen_keys[key]}: BUY {order['qty']} {order['symbol']} for {value:,.0f}"


if __name__ == "__main__":
    gate = ActionGate()

    def order(key, sym, qty, hour=11):
        return {"idempotency_key": key, "symbol": sym, "qty": qty, "hour": hour}

    steps = [
        ("small order, dry-run first",  order("k1", "INFY", 5), True),
        ("same order for real",         order("k1", "INFY", 5), False),
        ("agent retries same request",  order("k1", "INFY", 5), False),
        ("medium order",                order("k2", "TCS", 10), False),
        ("huge order",                  order("k3", "TCS", 100), False),
        ("after market hours",          order("k4", "INFY", 1, hour=20), False),
        ("runaway loop: many orders",   None, False),
    ]
    for label, o, dry in steps:
        if o is None:
            print(f"\n{label}:")
            executed = 0
            for i in range(1, 40):                      # a buggy agent keeps proposing 20,000 orders
                r = gate.submit(order(f"loop{i}", "TCS", 5))
                if r.startswith("EXECUTED"):
                    executed += 1
                else:
                    print(f"   loop order #{i}: {r}")
                    break
            print(f"   -> {executed} orders went through, then the DAILY LIMIT stopped the loop")
            continue
        print(f"{label:<28} -> {gate.submit(o, dry_run=dry)}")
    print("\nUNDO LOG (how to reverse what the agent did):")
    for u in gate.undo_log:
        print("  ", u)
    print(f"\nDaily notional used: {gate.daily_notional:,.0f} of {DAILY_LIMIT:,.0f}")
