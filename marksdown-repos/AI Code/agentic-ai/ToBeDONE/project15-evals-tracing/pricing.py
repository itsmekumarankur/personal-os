"""Token prices and cost maths.  cost = tokens / 1,000,000 * price per million, summed over the token kinds."""
import json
import os
from pathlib import Path

DEFAULT_PATH = Path(os.environ.get("PRICING_FILE", Path(__file__).parent / "pricing" / "pricing.json"))


class UnknownModel(KeyError):
    pass


def load_pricing(path=None) -> dict:
    data = json.loads(Path(path or DEFAULT_PATH).read_text(encoding="utf-8"))
    return {k: v for k, v in data.items() if not k.startswith("_")}


def cost_usd(pricing: dict, model: str, input_tokens=0, output_tokens=0, cache_read=0, cache_write=0) -> float:
    """Unknown model raises. A silent 0 would make dashboards say 'free' for a model you forgot to price."""
    if model not in pricing:
        raise UnknownModel(f"no price for model {model!r}; add it to the pricing file")
    p = pricing[model]
    return (input_tokens * p["input"] + output_tokens * p["output"]
            + cache_read * p.get("cache_read", p["input"]) + cache_write * p.get("cache_write", p["input"])) / 1_000_000


def trace_totals(spans: list) -> dict:
    """Add up what a whole trace used."""
    t = {"input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0, "llm_calls": 0, "tool_calls": 0, "errors": 0}
    for s in spans:
        a = s.attrs
        if a.get("gen_ai.operation.name") == "chat":
            t["llm_calls"] += 1
            t["input_tokens"] += a.get("gen_ai.usage.input_tokens", 0)
            t["output_tokens"] += a.get("gen_ai.usage.output_tokens", 0)
            t["cost_usd"] += a.get("cost.usd", 0.0)
        if a.get("gen_ai.operation.name") == "execute_tool":
            t["tool_calls"] += 1
        if s.status == "ERROR":
            t["errors"] += 1
    t["cost_usd"] = round(t["cost_usd"], 8)
    return t
