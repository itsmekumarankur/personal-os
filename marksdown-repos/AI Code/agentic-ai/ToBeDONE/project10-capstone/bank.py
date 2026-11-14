"""Sample bank back end (made-up data, in memory). In a real system this is your core banking API.

The platform never lets the model name an account: tools work on the caller's own account, and any
id the model does supply (card, transaction) is checked to belong to that account (see tools.py).
"""
import copy
import json


def _initial():
    return {
        "accounts": {
            "A-1001": {"holder": "Sample Customer One", "type": "savings", "balance": 125000.50, "currency": "INR"},
            "A-1002": {"holder": "Sample Customer Two", "type": "current", "balance": 48250.00, "currency": "INR"},
        },
        "cards": {
            "C-9001": {"account_id": "A-1001", "status": "active", "last4": "4242"},
            "C-9002": {"account_id": "A-1002", "status": "active", "last4": "1881"},
        },
        "transactions": {
            "A-1001": [
                {"txn_id": "T-5001", "date": "2026-09-28", "description": "Salary credit", "amount": 85000.00},
                {"txn_id": "T-5002", "date": "2026-09-27", "description": "Electricity bill", "amount": -2450.75},
                {"txn_id": "T-5003", "date": "2026-09-25", "description": "Online store", "amount": -3120.00},
                {"txn_id": "T-5004", "date": "2026-09-22", "description": "Mutual fund SIP", "amount": -10000.00},
            ],
            "A-1002": [
                {"txn_id": "T-6001", "date": "2026-09-29", "description": "Customer payment", "amount": 22000.00},
                {"txn_id": "T-6002", "date": "2026-09-26", "description": "Supplier payment", "amount": -15500.00},
            ],
        },
        "refunds": [],
    }


class Bank:
    def __init__(self):
        self._d = _initial()

    # ----- reads -----
    def account_summary(self, account_id: str) -> dict:
        return {"account_id": account_id, **copy.deepcopy(self._d["accounts"][account_id])}

    def transactions(self, account_id: str, limit: int) -> list[dict]:
        return copy.deepcopy(self._d["transactions"].get(account_id, [])[:limit])

    def transaction(self, account_id: str, txn_id: str) -> dict | None:
        return next((copy.deepcopy(t) for t in self._d["transactions"].get(account_id, []) if t["txn_id"] == txn_id), None)

    def card(self, card_id: str) -> dict | None:
        c = self._d["cards"].get(card_id)
        return copy.deepcopy(c) if c else None

    # ----- writes -----
    def freeze_card(self, card_id: str) -> None:
        self._d["cards"][card_id]["status"] = "frozen"

    def add_refund(self, account_id: str, txn_id: str, amount: float, reason: str) -> dict:
        refund = {"refund_id": f"R-{len(self._d['refunds']) + 1:04d}", "account_id": account_id,
                  "txn_id": txn_id, "amount": round(amount, 2), "reason": reason, "status": "queued"}
        self._d["refunds"].append(refund)
        return copy.deepcopy(refund)

    def refunds(self) -> list[dict]:
        return copy.deepcopy(self._d["refunds"])


def emi(principal: float, annual_rate_percent: float, months: int) -> dict:
    """Monthly instalment: P*r*(1+r)^n / ((1+r)^n - 1), r = monthly rate."""
    if not 0 < principal <= 1_000_000_000:
        raise ValueError("principal must be more than 0 and at most 1,000,000,000")
    if not 0 <= annual_rate_percent <= 100:
        raise ValueError("annual_rate_percent must be between 0 and 100")
    if not 1 <= months <= 480:
        raise ValueError("months must be between 1 and 480")
    r = annual_rate_percent / 12 / 100
    monthly = principal / months if r == 0 else principal * r * (1 + r) ** months / ((1 + r) ** months - 1)
    total = monthly * months
    return {"monthly_emi": round(monthly, 2), "total_payable": round(total, 2),
            "total_interest": round(total - principal, 2)}


def as_text(value) -> str:
    return json.dumps(value, indent=2)
