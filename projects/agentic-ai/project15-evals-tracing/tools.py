"""Two small tools for the agent under test (a bank support bot)."""
FEES = {"credit_card_annual": 500.0, "late_payment": 750.0, "atm_other_bank": 21.0}


def calculate_emi(principal: float, annual_rate_pct: float, months: int) -> str:
    if principal <= 0 or months <= 0 or annual_rate_pct < 0:
        raise ValueError("principal and months must be positive, rate cannot be negative")
    r = annual_rate_pct / 12 / 100
    emi = principal / months if r == 0 else principal * r * (1 + r) ** months / ((1 + r) ** months - 1)
    return f"{emi:.2f}"


def lookup_fee(product: str) -> str:
    if product not in FEES:
        raise ValueError(f"unknown product {product!r}; known: {', '.join(sorted(FEES))}")
    return f"{FEES[product]:.2f}"


TOOLS = {"calculate_emi": calculate_emi, "lookup_fee": lookup_fee}
TOOL_SCHEMAS = [
    {"name": "calculate_emi", "description": "Monthly instalment (EMI) for a loan.",
     "input_schema": {"type": "object", "properties": {"principal": {"type": "number"}, "annual_rate_pct": {"type": "number"},
                                                       "months": {"type": "integer"}}, "required": ["principal", "annual_rate_pct", "months"]}},
    {"name": "lookup_fee", "description": "Look up a bank fee in rupees. Products: " + ", ".join(sorted(FEES)),
     "input_schema": {"type": "object", "properties": {"product": {"type": "string"}}, "required": ["product"]}},
]
