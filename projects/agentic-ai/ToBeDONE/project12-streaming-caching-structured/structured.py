"""Structured output you can trust: three layers, each catches a different kind of wrong.

  LAYER 1  force the shape       give the model ONE tool whose input_schema is your schema and set tool_choice to that tool.
                                 The model must 'call' it, so you get an object, not prose. (Fenced JSON in text is the fallback, not the plan.)
  LAYER 2  validate the types    Pydantic: right fields, right types, ranges, enums, dates.             -> "schema" errors
  LAYER 3  validate the MEANING  rules the schema cannot say: items add up to total, vendor really occurs
                                 in the source text, date not in the future.                              -> "semantic" errors
  REPAIR   on failure send the exact errors back as an is_error tool_result and let the model fix them, at most N times,
           then FAIL LOUDLY. A valid-looking wrong answer that slips through is worse than an error.

Valid JSON != correct values. 'hallucinating' mode in fake_model.py produces perfectly valid JSON that is wrong. Only layer 3 sees it.
"""
import datetime as dt
import json
import re
from dataclasses import dataclass, field

from pydantic import BaseModel, Field, ValidationError, field_validator


class LineItem(BaseModel):
    description: str = Field(min_length=1)
    quantity: int = Field(gt=0, le=10_000)
    unit_price: float = Field(ge=0)


class Invoice(BaseModel):
    invoice_no: str = Field(pattern=r"^[A-Z]{2,5}-\d{2,8}$")
    vendor: str = Field(min_length=2, max_length=120)
    date: dt.date
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    items: list[LineItem] = Field(min_length=1)
    total: float = Field(ge=0)

    @field_validator("currency")
    @classmethod
    def known_currency(cls, v):
        if v not in {"INR", "USD", "EUR", "GBP"}:
            raise ValueError("currency must be one of INR, USD, EUR, GBP")
        return v


TOOL_NAME = "record_invoice"


def tool_for(model: type[BaseModel], name: str = TOOL_NAME, description: str = "Record the invoice exactly as written in the document.") -> dict:
    schema = model.model_json_schema()
    schema.pop("title", None)
    return {"name": name, "description": description, "input_schema": schema}


def request_for(source_text: str, system: str = "You extract invoices. Use only what the document says.", cache_system: bool = True) -> dict:
    sys_block = {"type": "text", "text": system}
    if cache_system:
        sys_block["cache_control"] = {"type": "ephemeral"}
    return {"model": "fake-sonnet", "max_tokens": 800, "system": [sys_block], "tools": [tool_for(Invoice)],
            "tool_choice": {"type": "tool", "name": TOOL_NAME}, "messages": [{"role": "user", "content": source_text}]}


# ---------------------------------------------------------------- layer 2 and 3
def schema_errors(data) -> tuple:
    try:
        return Invoice.model_validate(data), []
    except ValidationError as e:
        return None, [f"{'.'.join(str(x) for x in err['loc']) or 'input'}: {err['msg']}" for err in e.errors()]


def semantic_errors(inv: Invoice, source_text: str, today: dt.date | None = None) -> list:
    errs = []
    today = today or dt.date.today()
    calc = round(sum(i.quantity * i.unit_price for i in inv.items), 2)
    if abs(calc - inv.total) > 0.01:
        errs.append(f"total: items add up to {calc} but total says {inv.total}")
    if inv.vendor not in source_text:
        errs.append(f"vendor: '{inv.vendor}' does not appear in the document")
    if inv.invoice_no not in source_text:
        errs.append(f"invoice_no: '{inv.invoice_no}' does not appear in the document")
    if inv.date > today:
        errs.append(f"date: {inv.date} is in the future")
    for i in inv.items:
        if i.description not in source_text:
            errs.append(f"items: description '{i.description}' does not appear in the document")
    return errs


class ExtractionFailed(Exception):
    def __init__(self, attempts):
        super().__init__(f"gave up after {len(attempts)} attempts; last errors: {attempts[-1]['errors']}")
        self.attempts = attempts


@dataclass
class Extraction:
    value: Invoice
    attempts: list = field(default_factory=list)
    usage_total: dict = field(default_factory=dict)


def _add(a: dict, b: dict) -> dict:
    return {k: a.get(k, 0) + b.get(k, 0) for k in ("input_tokens", "output_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")}


def extract(call, source_text: str, max_attempts: int = 3, semantic: bool = True, today: dt.date | None = None, cache_system: bool = True) -> Extraction:
    """call(request) -> Message dict (non-streaming). Returns a validated Invoice or raises ExtractionFailed."""
    req = request_for(source_text, cache_system=cache_system)
    attempts, usage = [], {}
    for n in range(1, max_attempts + 1):
        msg = call(req)
        usage = _add(usage, msg["usage"])
        tool = next((b for b in msg["content"] if b["type"] == "tool_use" and b["name"] == TOOL_NAME), None)
        if tool is None:
            errs, kind = ["no tool call returned"], "no_tool"
        else:
            inv, errs = schema_errors(tool["input"])
            kind = "schema"
            if inv is not None and semantic:
                errs, kind = semantic_errors(inv, source_text, today), "semantic"
            if not errs:
                attempts.append({"attempt": n, "ok": True, "kind": "ok", "errors": []})
                return Extraction(inv, attempts, usage)
        attempts.append({"attempt": n, "ok": False, "kind": kind, "errors": errs})
        if tool is None:
            break
        # repair turn: the model's own call + the errors, as an is_error tool_result
        req = {**req, "messages": req["messages"][:1] + [
            {"role": "assistant", "content": [{"type": "tool_use", "id": tool["id"], "name": TOOL_NAME, "input": tool["input"]}]},
            {"role": "user", "content": [{"type": "tool_result", "tool_use_id": tool["id"], "is_error": True,
                                          "content": "Validation failed. Fix ONLY these problems and call the tool again:\n- " + "\n- ".join(errs)}]}]}
    raise ExtractionFailed(attempts)


def tolerant_json_from_text(text: str):
    """FALLBACK ONLY (model answered in prose): pull the first JSON object out, even inside a ```json fence. Still must pass layers 2 and 3."""
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.S) or re.search(r"(\{.*\})", text, re.S)
    if not m:
        raise ValueError("no JSON object found")
    return json.loads(m.group(1))
