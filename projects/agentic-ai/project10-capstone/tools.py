"""The tools the model may use. This file is where AUTHORIZATION lives.

Rules that make the tools safe even if the model is confused or manipulated:
  1. The model never supplies an account id. Tools act on the caller's own account, taken from the API key.
  2. Any other id the model supplies (a card, a transaction) is checked to belong to that account.
  3. Every tool validates its arguments in code before anything runs.
  4. Tools are marked "read" or "write". Write tools never run directly: a human must approve first
     (agent.py), and validation runs again at execution time because things may have changed.
"""
from dataclasses import dataclass
from typing import Callable

import bank as bank_mod
from config import Principal, Settings


class ToolRejected(Exception):
    """The request is not allowed or not valid. The message is safe to show the model."""


@dataclass
class ToolContext:
    principal: Principal
    bank: bank_mod.Bank
    settings: Settings


@dataclass
class Tool:
    name: str
    description: str
    properties: dict
    required: list
    risk: str                                              # "read" or "write"
    validate: Callable[[ToolContext, dict], dict]          # returns clean args or raises ToolRejected
    run: Callable[[ToolContext, dict], str]
    describe: Callable[[dict], str] = lambda args: ""      # for the human reviewer

    def schema(self) -> dict:
        return {"name": self.name, "description": self.description,
                "input_schema": {"type": "object", "properties": self.properties, "required": self.required}}


def _num(args: dict, key: str) -> float:
    v = args.get(key)
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        raise ToolRejected(f"{key} must be a number")
    return float(v)


def _text(args: dict, key: str, max_len: int, required: bool = True) -> str:
    v = args.get(key, "")
    if not isinstance(v, str) or (required and not v.strip()):
        raise ToolRejected(f"{key} must be a non-empty text")
    return v.strip()[:max_len]


# ---------- read tools ----------

def _no_args(ctx, args):
    return {}


def _summary_run(ctx, args):
    return bank_mod.as_text(ctx.bank.account_summary(ctx.principal.account_id))


def _tx_validate(ctx, args):
    limit = args.get("limit", 5)
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 20:
        raise ToolRejected("limit must be a whole number from 1 to 20")
    return {"limit": limit}


def _tx_run(ctx, args):
    return bank_mod.as_text(ctx.bank.transactions(ctx.principal.account_id, args["limit"]))


def _emi_validate(ctx, args):
    clean = {"principal": _num(args, "principal"), "annual_rate_percent": _num(args, "annual_rate_percent")}
    months = args.get("months")
    if isinstance(months, bool) or not isinstance(months, int):
        raise ToolRejected("months must be a whole number")
    clean["months"] = months
    try:
        bank_mod.emi(**clean)
    except ValueError as e:
        raise ToolRejected(str(e)) from e
    return clean


def _emi_run(ctx, args):
    return bank_mod.as_text(bank_mod.emi(**args))


# ---------- write tools (need human approval) ----------

def _freeze_validate(ctx, args):
    card_id = _text(args, "card_id", 20)
    card = ctx.bank.card(card_id)
    if card is None or card["account_id"] != ctx.principal.account_id:
        raise ToolRejected("No such card on your account.")          # same answer for "missing" and "someone else's"
    if card["status"] != "active":
        raise ToolRejected(f"Card {card_id} is already {card['status']}.")
    return {"card_id": card_id, "reason": _text(args, "reason", 200, required=False)}


def _freeze_run(ctx, args):
    ctx.bank.freeze_card(args["card_id"])
    return f"Card {args['card_id']} is now frozen."


def _refund_validate(ctx, args):
    txn_id = _text(args, "txn_id", 20)
    amount = round(_num(args, "amount"), 2)
    txn = ctx.bank.transaction(ctx.principal.account_id, txn_id)
    if txn is None:
        raise ToolRejected("No such transaction on your account.")
    if txn["amount"] >= 0:
        raise ToolRejected("Only debits can be refunded.")
    if amount <= 0:
        raise ToolRejected("amount must be more than 0")
    if amount > abs(txn["amount"]):
        raise ToolRejected(f"amount cannot be more than the transaction ({abs(txn['amount'])}).")
    if amount > ctx.settings.max_refund:
        raise ToolRejected(f"Refunds above {ctx.settings.max_refund:g} cannot be requested here. "
                           "Tell the customer to contact a branch.")
    return {"txn_id": txn_id, "amount": amount, "reason": _text(args, "reason", 200)}


def _refund_run(ctx, args):
    r = ctx.bank.add_refund(ctx.principal.account_id, args["txn_id"], args["amount"], args["reason"])
    return f"Refund {r['refund_id']} of {r['amount']} queued for transaction {r['txn_id']}."


TOOLS: dict[str, Tool] = {t.name: t for t in [
    Tool("get_account_summary", "Get the balance and type of the customer's own account.",
         {}, [], "read", _no_args, _summary_run),
    Tool("list_transactions", "List the customer's most recent transactions, newest first. limit is 1 to 20.",
         {"limit": {"type": "integer"}}, [], "read", _tx_validate, _tx_run),
    Tool("calculate_emi", "Calculate the monthly loan instalment (EMI). Does not use any account data.",
         {"principal": {"type": "number"}, "annual_rate_percent": {"type": "number"}, "months": {"type": "integer"}},
         ["principal", "annual_rate_percent", "months"], "read", _emi_validate, _emi_run),
    Tool("freeze_card", "Request to freeze one of the customer's cards. A human reviewer must approve first.",
         {"card_id": {"type": "string"}, "reason": {"type": "string"}}, ["card_id"], "write",
         _freeze_validate, _freeze_run, lambda a: f"Freeze card {a['card_id']} ({a.get('reason') or 'no reason given'})"),
    Tool("raise_refund", "Request a refund for one debit transaction of the customer. A human reviewer must approve first.",
         {"txn_id": {"type": "string"}, "amount": {"type": "number"}, "reason": {"type": "string"}},
         ["txn_id", "amount", "reason"], "write", _refund_validate, _refund_run,
         lambda a: f"Refund {a['amount']:g} for transaction {a['txn_id']} ({a['reason']})"),
]}


def tool_schemas() -> list[dict]:
    return [t.schema() for t in TOOLS.values()]
