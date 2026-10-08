"""The business logic. Plain Python, no MCP, no AI.

Keeping this separate from server.py means the logic can be tested (and reused) without
any protocol code. The data below is made-up sample data.
"""
import json

ACCOUNTS = {
    "A-1001": {"holder": "Sample Customer One", "type": "savings", "balance": 125000.50, "currency": "INR"},
    "A-1002": {"holder": "Sample Customer Two", "type": "current", "balance": 48250.00, "currency": "INR"},
}

TRANSACTIONS = {
    "A-1001": [
        {"date": "2026-09-28", "description": "Salary credit", "amount": 85000.00},
        {"date": "2026-09-27", "description": "Electricity bill", "amount": -2450.75},
        {"date": "2026-09-25", "description": "Grocery store", "amount": -3120.00},
        {"date": "2026-09-22", "description": "Mutual fund SIP", "amount": -10000.00},
        {"date": "2026-09-20", "description": "Restaurant", "amount": -1800.00},
        {"date": "2026-09-18", "description": "Refund", "amount": 650.00},
    ],
    "A-1002": [
        {"date": "2026-09-29", "description": "Customer payment", "amount": 22000.00},
        {"date": "2026-09-26", "description": "Supplier payment", "amount": -15500.00},
    ],
}

FEES_POLICY = """Sample fee policy (made-up text for this exercise)
- Savings account: no monthly fee above a balance of 10,000.
- Current account: monthly fee of 250 below a balance of 25,000.
- Loan prepayment: no charge on floating-rate loans."""


def emi(principal: float, annual_rate_percent: float, months: int) -> dict:
    """Monthly instalment for a loan: P*r*(1+r)^n / ((1+r)^n - 1), r = monthly rate."""
    if not 0 < principal <= 1_000_000_000:
        raise ValueError("principal must be more than 0 and at most 1,000,000,000")
    if not 0 <= annual_rate_percent <= 100:
        raise ValueError("annual_rate_percent must be between 0 and 100")
    if not 1 <= months <= 480:
        raise ValueError("months must be between 1 and 480")
    r = annual_rate_percent / 12 / 100
    if r == 0:
        monthly = principal / months
    else:
        growth = (1 + r) ** months
        monthly = principal * r * growth / (growth - 1)
    total = monthly * months
    return {
        "monthly_emi": round(monthly, 2),
        "total_payable": round(total, 2),
        "total_interest": round(total - principal, 2),
    }


def account_summary(account_id: str) -> dict:
    account = ACCOUNTS.get(account_id)
    if account is None:
        raise ValueError(f"unknown account_id: {account_id!r}")
    return {"account_id": account_id, **account}


def transactions(account_id: str, limit: int = 5) -> list[dict]:
    if account_id not in TRANSACTIONS:
        raise ValueError(f"unknown account_id: {account_id!r}")
    if not 1 <= limit <= 20:
        raise ValueError("limit must be between 1 and 20")
    return TRANSACTIONS[account_id][:limit]


def as_text(value) -> str:
    return json.dumps(value, indent=2)
