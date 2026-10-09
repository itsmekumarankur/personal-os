"""Fake bank data. Every record has an owner, so tools can check 'is this yours?'."""
ACCOUNTS = {
    "acc-1": {"customer": "cust-1001", "type": "savings", "balance": 125000.50},
    "acc-2": {"customer": "cust-1001", "type": "current", "balance": 8200.00},
    "acc-9": {"customer": "cust-2002", "type": "savings", "balance": 999999.00},     # somebody else's account
}
TRANSACTIONS = {
    "acc-1": [("2025-01-03", -2500.0, "Rent"), ("2025-01-05", 85000.0, "Salary"), ("2025-01-09", -420.5, "Groceries")],
    "acc-2": [("2025-01-02", -120.0, "Fuel")],
    "acc-9": [("2025-01-04", -50000.0, "Private payment")],
}
CARDS = {"card-1": {"customer": "cust-1001", "status": "active"}, "card-9": {"customer": "cust-2002", "status": "active"}}


class NotYours(Exception):
    pass


def _owned(table: dict, key: str, customer: str):
    rec = table.get(key)
    if rec is None or rec["customer"] != customer:
        raise NotYours(f"{key} not found")           # same message for 'missing' and 'not yours', so ids cannot be probed


def calculate_emi(principal: float, annual_rate_pct: float, months: int) -> dict:
    if principal <= 0 or months <= 0 or annual_rate_pct < 0:
        raise ValueError("principal and months must be positive, rate cannot be negative")
    r = annual_rate_pct / 12 / 100
    emi = principal / months if r == 0 else principal * r * (1 + r) ** months / ((1 + r) ** months - 1)
    return {"emi": round(emi, 2), "total_payable": round(emi * months, 2), "total_interest": round(emi * months - principal, 2)}


def account_summary(account_id: str, customer: str) -> dict:
    _owned(ACCOUNTS, account_id, customer)
    a = ACCOUNTS[account_id]
    return {"account_id": account_id, "type": a["type"], "balance": a["balance"]}


def list_transactions(account_id: str, customer: str, limit: int = 10) -> list:
    _owned(ACCOUNTS, account_id, customer)
    return [{"date": d, "amount": amt, "note": n} for d, amt, n in TRANSACTIONS[account_id][-max(1, min(limit, 50)):]]


def freeze_card(card_id: str, customer: str) -> dict:
    _owned(CARDS, card_id, customer)
    CARDS[card_id]["status"] = "frozen"
    return {"card_id": card_id, "status": "frozen"}
